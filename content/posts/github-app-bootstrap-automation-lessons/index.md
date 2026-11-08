---
author: Gunn Kim
cover:
  alt: GitHub App Bootstrap을 자동화하며 만난 여섯 개의 함정 대표 이미지
  hiddenInList: false
  hiddenInSingle: false
  image: https://gunn.kim/covers/github-app-bootstrap.jpg
date: '2026-07-20'
description: 최소 권한 GitHub App bootstrap을 자동화하며 만난 manifest 필드, CSRF state, App JWT
  Bearer 인증, 부분 생성 복구, token 폐기 문제와 해결 원칙을 정리합니다.
draft: false
keywords: &id001
- DevOps
- API
- 트러블슈팅
- CI/CD
lastmod: '2026-11-08T15:46:00.000Z'
notion_id: 3a37522e-eb2f-816f-adea-fc7cd1ea9de3
slug: "github-app-bootstrap-automation-lessons"
subtitle: Manifest부터 App JWT, installation token 폐기까지 실제 자동화에서 확인한 GitHub App 보안 계약
summary: 최소 권한 GitHub App bootstrap을 자동화하며 만난 manifest 필드, CSRF state, App JWT Bearer
  인증, 부분 생성 복구, token 폐기 문제와 해결 원칙을 정리합니다.
tags: *id001
title: GitHub App Bootstrap을 자동화하며 만난 여섯 개의 함정
---

GitHub Actions의 기본 `GITHUB_TOKEN`만으로도 많은 자동화를 만들 수 있다. 하지만 자동화가 Pull Request를 만들고, 그 PR이 다시 CI를 정상적으로 촉발해야 하는 순간에는 별도의 GitHub App이 필요해질 수 있다.

이번 작업의 목표는 단순했다.

1. 최소 권한 GitHub App을 만든다.
1. 특정 저장소 하나에만 설치한다.
1. 1시간 이하의 installation token을 발급한다.
1. 권한과 저장소 범위를 검증한다.
1. token을 즉시 폐기한다.
1. 다음 자동화가 사용할 App ID, bot ID, private key를 GitHub Actions 설정에 안전하게 저장한다.
결과적으로 bootstrap은 성공했다. 그러나 “App 생성 버튼 한 번 누르면 끝”이라고 생각했던 흐름은 manifest, 인증 주체, API 수명주기, secret 처리 방식이 맞물린 작은 보안 프로토콜에 가까웠다. 이 글은 그 과정에서 실제로 만난 실패와, 재사용할 수 있는 설계 원칙을 정리한 기록이다.

# 최종 결과

최종 live probe의 redacted 결과는 다음과 같았다.

```plain text
outcome=pass\ntoken_ttl_seconds=3599\ntoken_discarded=true\nrepositories=정확히 1개\ncontents=write\nmetadata=read\npull_requests=write\nwebhook_events=none\nsecret_leak=false
```

Private key, JWT, installation token, PAT 값은 출력하지 않았다. 결과 문서에도 credential 값이나 파일 경로를 남기지 않았다.

# 전체 흐름부터 이해하기

GitHub App bootstrap에는 서로 다른 세 종류의 인증 수단이 등장한다.

```plain text
사용자 인증\n  └─ App manifest를 제출하고 App을 생성한다\n\nApp JWT\n  ├─ App 설치 목록을 조회한다\n  └─ installation token을 발급한다\n\nInstallation token\n  ├─ 설치된 저장소 범위를 확인한다\n  ├─ 실제 App 권한을 검증한다\n  └─ 검증 직후 폐기한다
```

이 셋은 서로 대체할 수 없다. 사용자 PAT로 App 전용 endpoint를 호출하거나, JWT를 일반 access token 방식으로 전송하면 인증에 실패한다. bootstrap 구현은 “토큰 문자열 하나”가 아니라 “누가 어떤 자격으로 어떤 endpoint를 호출하는가”를 모델링해야 한다.

# 함정 1. 비활성 webhook에도 URL이 필요했다

첫 오류는 다음과 같았다.

```plain text
Invalid GitHub App configuration\nError "url" wasn't supplied.
```

manifest에는 이미 App homepage를 나타내는 top-level `url`이 있었다. 빠진 것은 `hook_attributes.url`이었다.

```json
{\n  "url": "https://github.com/OWNER/REPO",\n  "hook_attributes": {\n    "active": false,\n    "url": "https://github.com/OWNER/REPO"\n  },\n  "default_events": []\n}
```

webhook delivery를 비활성화하고 event도 하나도 구독하지 않더라도, manifest 계약상 hook URL은 제공해야 했다. “사용하지 않으니 생략 가능할 것”이라는 추정이 API schema와 달랐다.

GitHub의 [App manifest 문서](https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-from-a-manifest)는 top-level `url`과 `hook_attributes.url`을 서로 다른 필드로 정의한다. 오류 메시지가 어느 `url`을 가리키는지 모호할 수 있으므로 두 계약을 분리해서 검증하는 편이 좋다.

# 함정 2. `state`는 redirect URL에 넣는 값이 아니었다

두 번째 오류는 다음과 같았다.

```plain text
Error redirect_url must be a valid URL
```

처음에는 loopback HTTP URL 자체가 거절된다고 생각했다. 그러나 문제는 CSRF 방어용 `state`를 `redirect_url`의 query string에 넣은 것이었다.

잘못된 형태는 다음과 같다.

```plain text
redirect_url=http://127.0.0.1:PORT/callback?state=RANDOM
```

manifest flow에서 `state`는 GitHub App 생성 POST URL의 별도 파라미터로 전달해야 한다.

```html
<form\n  method="post"\n  action="https://github.com/settings/apps/new?state=RANDOM"\n>\n  <input type="hidden" name="manifest" value="...">\n</form>
```

그리고 manifest의 redirect URL은 callback 위치만 나타낸다.

```plain text
http://127.0.0.1:PORT/callback
```

GitHub는 callback 시 `code`와 `state`를 다시 전달한다. 로컬 helper는 예측 불가능한 state를 생성하고, callback의 state가 정확히 일치할 때만 manifest conversion을 진행해야 한다.

이 구분 덕분에 callback server는 계속 `127.0.0.1`에만 bind할 수 있었고, 임시 public tunnel을 만들 필요도 없었다.

# 함정 3. App 생성과 설치는 하나의 트랜잭션이 아니다

manifest conversion을 완료하면 App ID와 private key를 받을 수 있다. 그러나 그 시점에는 App이 특정 계정이나 저장소에 아직 설치되지 않았을 수 있다.

초기 구현은 App 생성 직후 bot 계정을 조회했다. 실제 흐름에서는 설치가 관찰된 뒤 bot identity를 검증하는 순서가 더 안전했다.

```plain text
manifest conversion\n  → App JWT 생성\n  → 설치 화면 열기\n  → App JWT로 설치 관찰\n  → bot identity 확인\n  → installation token 발급
```

여기서 더 중요한 운영 문제가 있었다. manifest conversion으로 받은 최초 private key는 일회성 응답이다. App 생성 후 secret 저장 전에 프로세스가 실패하면 다음 상태가 만들어질 수 있다.

```plain text
GitHub App: 존재\n설치: 존재할 수도 있음\n로컬 private key: 프로세스 종료로 소실\n저장소 secret: 아직 없음
```

이 부분 생성 상태를 정상 완료로 오해하면 안 된다. 선택지는 두 가지다.

1. 사람이 부분 생성 App을 삭제하고 수정된 helper로 다시 생성한다.
1. App 설정에서 새 private key를 발급하고 승인된 recovery 절차를 수행한다.
자동화가 임의로 App을 삭제해서도 안 된다. 삭제는 복구가 필요한 외부 자산 변경이므로 반드시 사람의 명시적 승인을 받아야 한다.

# 함정 4. 사용자 토큰으로 설치 목록을 조회할 수 없었다

초기 helper는 사용자의 `gh` 인증으로 다음 endpoint를 조회했다.

```plain text
GET /user/installations
```

하지만 bootstrap이 필요로 하는 것은 “현재 사용자가 접근할 수 있는 설치”가 아니라 “방금 생성한 App의 설치”다. 이 조회는 App JWT로 수행하는 것이 맞다.

```plain text
GET /app/installations\nAuthorization: Bearer APP_JWT
```

설치 대상을 찾을 때는 App ID만 믿기보다 설치 객체의 account ID가 기대한 소유자와 일치하는지도 확인해야 한다. 같은 App을 여러 계정에 설치할 수 있기 때문이다.

# 함정 5. JWT는 반드시 Bearer로 보내야 했다

가장 선명했던 인증 실패는 다음 단계에서 발생했다.

```plain text
stage=app/installations
```

JWT 서명 자체는 정상이었다. 문제는 전송 방식이었다. 일반 access token처럼 전달하면 GitHub App JWT로 인정되지 않는다.

GitHub의 [JWT 인증 문서](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app)는 JWT에 `Authorization: Bearer`를 사용해야 한다고 명시한다.

여기서 단순히 CLI 인자에 header를 넣는 방식도 피했다.

```bash
# 피해야 할 형태: 프로세스 목록에 JWT가 보일 수 있다.\nsome-command -H "Authorization: Bearer JWT_VALUE"
```

대신 Python의 HTTPS client에서 header를 메모리 안에서 구성했다.

```python
headers = {\n    "Accept": "application/vnd.github+json",\n    "Authorization": f"Bearer {jwt}",\n    "User-Agent": "app-bootstrap",\n}
```

이 방식은 shell interpolation을 피하고, JWT가 command argument나 실행 로그에 나타나는 위험을 줄인다. installation token도 같은 경계를 사용했다.

# 함정 6. 오래된 convenience endpoint에 의존하면 안 됐다

installation token 발급까지 성공한 뒤 다음 호출이 404를 반환했다.

```plain text
GET /installation
```

이 호출은 꼭 필요하지 않았다. 이미 App JWT로 받은 installation 객체에 App ID, repository selection, permissions가 들어 있었다. installation token으로는 실제 접근 가능한 저장소 목록만 확인하면 충분했다.

최종 검증은 다음 두 증거를 결합했다.

```plain text
App JWT로 받은 installation 객체\n  +\ninstallation token으로 받은 /installation/repositories 결과
```

중복 확인을 위해 legacy endpoint를 하나 더 호출하는 것은 안전성을 높이지 않았다. 오히려 API 변화에 대한 실패 지점만 추가했다.

# Redaction과 진단 가능성의 균형

초기 실패 보고는 모든 API 오류를 다음처럼 표시했다.

```plain text
error_code=command_failed\nstage=api
```

secret 유출은 막았지만 어느 호출이 실패했는지 알 수 없어 디버깅 비용이 컸다. 반대로 endpoint 전체를 그대로 출력하면 manifest conversion code나 installation ID 같은 불필요한 값이 기록될 수 있다.

최종적으로 다음 원칙을 사용했다.

- secret이 포함될 수 있는 경로는 `manifest_conversion`, `installation_token` 같은 고정 별칭으로 기록한다.
- 안전한 endpoint는 query string을 제거한 stage만 기록한다.
- HTTP 오류는 `http_403`, `http_404`, `http_422`, `http_429`처럼 구분한다.
- response body, 인증 header, token 값은 기록하지 않는다.
좋은 redaction은 “아무 정보도 남기지 않는 것”이 아니다. 비밀을 제거하면서도 다음 조치를 결정할 수 있는 최소한의 구조적 증거를 남기는 것이다.

# Installation token은 사용 후 바로 폐기한다

installation token은 최대 1시간 동안 유효하다. 이번 probe에서는 TTL이 3599초임을 확인했고, 검증 직후 다음 정리 요청을 실행했다.

```plain text
DELETE /installation/token
```

폐기는 성공 경로에만 있으면 부족하다. repository scope 검증이나 권한 검증에서 예외가 발생해도 실행돼야 하므로 `finally`에 해당하는 정리 경계에 둬야 한다.

```python
token = create_installation_token()\ntry:\n    verify_permissions(token)\n    verify_repository_scope(token)\nfinally:\n    revoke_installation_token(token)
```

최종 PASS 조건에 `token_discarded=true`를 포함한 이유다.

# Secret 저장은 모든 검증 뒤에 한다

repository secret과 variables는 다음 검증이 모두 끝난 뒤에만 설정했다.

1. App manifest 권한과 event 계약
1. 설치 계정
1. `repository_selection=selected`
1. 선택된 저장소가 정확히 하나인지 여부
1. installation token TTL
1. 실제 token permissions
1. bot identity
1. token 폐기
그 후 다음 세 설정을 저장했다.

```plain text
APP_PRIVATE_KEY  → secret\nAPP_ID           → variable\nBOT_ID           → variable
```

설정 중간에 실패하면 이번 실행에서 생성한 항목만 역순으로 rollback한다. 기존 사용자의 설정이나 관련 없는 secret은 건드리지 않는다.

# 다음 설치를 위한 체크리스트

다음에 GitHub App bootstrap을 다시 구현한다면 아래 순서를 권한다.

[ ] fresh checkout에서 시작한다.
[ ] `gh auth status`를 확인한다.
[ ] 환경의 오래된 `GITHUB_TOKEN`과 `GH_TOKEN`이 keyring 인증을 가로채지 않는지 확인한다.
[ ] manifest의 homepage URL과 hook URL을 각각 검증한다.
[ ] state를 POST URL의 별도 파라미터로 전달한다.
[ ] callback server는 loopback에만 bind한다.
[ ] App JWT는 RS256으로 짧게 발급한다.
[ ] JWT는 반드시 Bearer header로 전송한다.
[ ] App 설치는 App JWT로 관찰한다.
[ ] bot은 설치 이후 확인한다.
[ ] installation token의 TTL, 권한, 저장소 범위를 검증한다.
[ ] token은 성공과 실패 모두에서 폐기한다.
[ ] 모든 검증 뒤에만 secret과 variables를 저장한다.
[ ] 최종 결과에는 redacted 필드만 남긴다.
[ ] mock 성공과 live GitHub 성공을 구분한다.
# 마무리

GitHub App bootstrap은 UI 자동화 문제가 아니었다. 핵심은 서로 다른 인증 주체와 일회성 credential의 수명주기를 안전하게 연결하는 일이었다.

이번 경험에서 가장 크게 남은 원칙은 세 가지다.

첫째, API 문서의 필드와 인증 주체를 추정하지 말고 계약으로 다룬다. 둘째, secret을 숨기는 것과 실패 원인을 관찰할 수 있게 만드는 것을 동시에 설계한다. 셋째, 외부 자산 생성은 중간 실패를 전제로 recovery와 rollback 경계를 먼저 만든다.

최종적으로 App은 단일 저장소에 최소 권한으로 설치됐고, 1시간 이하 token의 발급과 폐기까지 live로 검증됐다. 이제 이 결과를 “한 번 성공한 수작업”이 아니라 다음 실행에서도 반복 가능한 운영 지식으로 남길 수 있게 됐다.

