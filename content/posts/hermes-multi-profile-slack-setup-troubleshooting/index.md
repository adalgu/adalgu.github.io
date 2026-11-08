---
author: Gunn Kim
date: '2026-05-27'
description: Hermes 멀티 프로필 기능을 활용해 다수의 Slack 워크스페이스에 봇을 연결하는 과정과, 연동 중 흔히 겪는 Slack
  토큰(xapp, xoxb) 충돌 및 `invalid_auth` 에러의 원인과 명확한 해결책을 공유합니다.
draft: false
keywords: &id001
- hermes
- slackbot
lastmod: '2026-06-14T06:05:00.000Z'
notion_id: 36d7522e-eb2f-800d-9791-c21eb13296e0
slug: "hermes-multi-profile-slack-setup-troubleshooting"
subtitle: 하나의 서버에서 여러 Slack 워크스페이스에 Hermes 에이전트 독립 연동 및 토큰 오류 해결 방법
summary: Hermes 멀티 프로필 기능을 활용해 다수의 Slack 워크스페이스에 봇을 연결하는 과정과, 연동 중 흔히 겪는 Slack 토큰(xapp,
  xoxb) 충돌 및 `invalid_auth` 에러의 원인과 명확한 해결책을 공유합니다.
tags: *id001
title: Hermes 멀티 프로필로 여러 Slack 워크스페이스에 에이전트 붙이기 — 그리고 invalid_auth 함정
---

## Hermes 멀티 프로필로 여러 Slack 워크스페이스에 에이전트 붙이기

한 대의 머신에서 Hermes Agent를 프로필(profile) 단위로 여러 개 띄우고, 각 프로필을 서로 다른 Slack 워크스페이스에 연결하는 방법 정리. 실제로 특정 프로필(`custom_profile`)을 새 워크스페이스(`New_Workspace`, team `T_NEW`)에 붙이다가 "연결된 것 같은데 답장을 안 하는" 증상으로 한참 헤맸고, 원인은 Slack bot 토큰 무효(`invalid_auth`) 였다. 다음에 프로필을 더 만들 때 같은 데서 막히지 않도록 과정을 통째로 박제해 둔다.

### 1. 큰 그림: 프로필이 뭐고 왜 쓰나

Hermes의 프로필은 완전히 격리된 인스턴스다. 각 프로필은 자기만의 `HERMES_HOME` 디렉토리를 가진다 — config, API 키(`.env`), 세션 DB, 메모리, 스킬, 게이트웨이 상태까지 전부 분리된다.

- **기본(루트) 인스턴스** → `~/.hermes/`
- **이름 있는 프로필** → `~/.hermes/profiles/<name>/`
내부적으로 `hermes -p <name> ...`를 주면 `_apply_profile_override()`가 **모든 모듈 import 전에** `HERMES_HOME`을 그 프로필 폴더로 바꿔치기한다. 그래서 코드 전역의 `get_hermes_home()`이 자동으로 해당 프로필로 스코프된다.

핵심 효과: 프로필마다 게이트웨이를 따로 띄울 수 있고, 각 게이트웨이가 다른 메신저 계정/워크스페이스에 붙는다. 우리 머신에선 지금 두 개가 동시에 돈다.

```plain text
PID 93729   루트 게이트웨이   → Slack: main_workspace.slack.com (team T_MAIN)
PID 71720   custom_profile 프로필 게이트웨이 → Slack: New_Workspace (team T_NEW)
```

두 게이트웨이가 같이 떠 있는 건 정상이다. 격리만 제대로 돼 있으면 충돌하지 않는다. "제대로 돼 있으면"이 함정의 핵심 — 아래 4·6장 참고.

### 2. 새 프로필 만들기 (단계별)

**1) 프로필 생성**

```plain text
hermes profile create <name>          # 예: hermes profile create custom_profile
hermes profile list                   # 생성 확인
```

**2) 이 프로필 컨텍스트로 설정 (모든 명령에 -p )**

```plain text
hermes -p <name> setup                # 전체 설정 마법사 (모델/툴/게이트웨이 한번에)

# 또는 메신저만:
hermes -p <name> gateway setup        # Slack/Telegram 등 플랫폼만 설정
```

**3) 게이트웨이 실행**

```plain text
hermes -p <name> gateway run          # 포그라운드 실행
hermes -p <name> gateway run --replace  # 기존 인스턴스 교체하며 실행
hermes -p <name> gateway status       # 상태 확인
```

- 프로필 관련 서브커맨드: `create`, `list`, `switch`, `use`, `delete`.
- **주의:** `hermes profile delete <name>`은 그 프로필의 `HERMES_HOME` 전체(세션·메모리 포함)를 날린다. 함부로 쓰지 말 것.
### 3. Slack 토큰 2종 — 여기서 90%가 막힌다

Hermes의 Slack 연동은 Socket Mode 기반이고, 토큰이 두 종류 필요하다. 이 둘의 역할이 다르고, 유효성이 따로 논다는 게 핵심이다.

<!-- notion-table: column_header=false row_header=false -->
| **.env 키**          | **토큰 형태**   | **용도**                       | **어디서 발급**                                                               |
|:--------------------|:------------|:-----------------------------|:-------------------------------------------------------------------------|
| **SLACK_APP_TOKEN** | `xapp-...`  | 이벤트 수신 (Socket Mode 연결)      | Slack 앱 → Basic Information → App-Level Tokens (`connections:write` 스코프) |
| **SLACK_BOT_TOKEN** | `xoxb-...`  | Web API 호출 (메시지 전송, 채널 조회 등) | Slack 앱 → OAuth & Permissions → Bot User OAuth Token (워크스페이스 설치 시 발급)    |

*추가로 보통 함께 두는 것들:*

- `SLACK_HOME_CHANNEL` — 기본 응답 채널/DM ID (예: `C0B5M...`)
- `SLACK_ALLOWED_USERS` — 허용 사용자 ID 목록 (예: `U1923...`)
**왜 둘로 나뉘는가**

- xapp (app-level token)은 앱 자체에 묶인다. 앱을 워크스페이스에 재설치해도 보통 그대로 살아남는다. → Socket Mode가 계속 붙는다.
- xoxb (bot token)은 "이 앱이 이 워크스페이스에 설치된 인스턴스" 에 묶인다. 앱을 재설치하거나 토큰을 재생성하면 값이 바뀐다. 옛 값은 즉시 무효가 된다.
- **결과적으로** xapp는 맞는데 xoxb만 틀린 어긋난 상태가 너무 쉽게 만들어진다. 이게 정확히 우리가 겪은 증상이다.

![](image-01.png)

### 4. 우리가 겪은 증상과 진단

**증상**

- 봇이 워크스페이스에 인증된 것처럼 보임. DM/멘션도 들어옴 (channel directory가 실시간 갱신됨).
- 그런데 답장을 안 함. "잘 되다가 안 되고 꼬인" 느낌.
**실제로 일어난 일**

게이트웨이 로그에 이게 5분마다 1,400번 넘게 찍히고 있었다:

```plain text
WARNING gateway.channel_directory: Channel directory: failed to list Slack channels
for team T_NEW: ... (url: https://slack.com/api/users.conversations, status: 200)
The server responded with: {'ok': False, 'error': 'invalid_auth'}
```

그리고 첫 인증 로그 바로 그 순간부터 깨져 있었다:

```plain text
2026-05-22 15:00:14 INFO  gateway.platforms.slack: [Slack] Authenticated as @bot_name
                          in workspace New_Workspace (team: T_NEW)   ← Socket Mode(xapp) OK
2026-05-22 15:00:14 WARN  ... users.conversations ... invalid_auth ← Web API(xoxb) 실패
```

<!-- notion-table: column_header=false row_header=false -->
| **토큰**                     | **상태**                                              |
|:---------------------------|:----------------------------------------------------|
| **SLACK_APP_TOKEN (xapp)** | ✅ 정상 — Socket Mode로 `New_Workspace`에 인증됨 → 이벤트는 들어옴 |
| **SLACK_BOT_TOKEN (xoxb)** | ❌ `invalid_auth` — 모든 답장/조회 API가 실패                 |

즉 받기만 하고 못 보내는 반쪽 연결. 겉보기엔 연결돼 보여서 더 헷갈렸다.

**결정적 확인 — auth.test**

토큰 유효성은 Slack `auth.test`(읽기 전용)로 1초 만에 판별된다. **토큰을 화면에 찍지 말고** `.env`에서 바로 읽어 헤더로 넘긴다:

```plain text
cd ~/.hermes
tok() { grep -E "^$2=" "$1" | head -1 | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//'; }

# 검증할 프로필의 bot 토큰
curl -s -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $(tok profiles/custom_profile/.env SLACK_BOT_TOKEN)" | python3 -m json.tool
```

- **정상이면:**JSON
```plain text
{ "ok": true, "url": "https://....slack.com/", "team": "...", "team_id": "T...", "user": "hermes", "bot_id": "B..." }
```

- **무효면:**JSON
```plain text
{ "ok": false, "error": "invalid_auth" }
```

우리 케이스: `custom_profile` bot 토큰 → `invalid_auth`, 루트 bot 토큰 → `ok: true`. 끝. 범인 확정.

**해결**

1. `New_Workspace` Slack 앱 → OAuth & Permissions → Bot User OAuth Token(`xoxb-`) 최신 값을 복사. (앱을 재설치/토큰 재생성했으면 값이 바뀌어 있다.)
- ⚠️ 이 bot 토큰은 지금 쓰는 app 토큰(`xapp`)과 같은 앱의 것이어야 한다. 서로 다른 앱의 토큰을 섞으면 정확히 이 증상(Socket은 붙는데 Web API는 `invalid_auth`)이 난다.
1. `~/.hermes/profiles/custom_profile/.env`의 `SLACK_BOT_TOKEN` 교체.
1. 게이트웨이 재시작 (아래 5장 — 이걸 안 해서 두 번 헤맸다).
1. `auth.test` 재확인 → `ok: true` 뜨면 끝.
### 5. 두 번째 함정: .env 고쳐도 재시작 안 하면 그대로

게이트웨이는 시작 시점에 `.env`를 메모리로 읽는다. 떠 있는 프로세스는 이후 `.env`를 고쳐도 반영하지 않는다. 우리 케이스 타임라인이 정확히 이거였다:

```plain text
custom_profile 게이트웨이 기동:   2026-05-22 15:18
custom_profile .env 마지막 수정:  2026-05-22 22:30   ← 기동 이후! → 실행 중 프로세스엔 미반영
```

토큰을 고쳐도 게이트웨이가 옛 토큰을 물고 있으니 계속 깨진 것처럼 보인다. → `.env`를 만졌으면 반드시 재시작.

```plain text
hermes -p custom_profile gateway restart      # 권장

# 또는
hermes -p custom_profile gateway run --replace # 기존 인스턴스 교체하며 포그라운드 실행
```

⚠️ `gateway stop/restart --all`은 모든 프로필의 게이트웨이를 전부 죽인다. 루트 게이트웨이까지 같이 내려가니, 특정 프로필만 만질 땐 `--all` 빼고 `-p <name>`만 줄 것.

### 6. 세 번째 함정: 프로필 간 토큰 공유 = 락 충돌

게이트웨이 플랫폼 어댑터는 고유 크리덴셜(봇 토큰)에 scoped lock을 건다. 두 프로필이 같은 토큰을 쓰면 나중에 뜬 쪽이 막힌다. 우리도 초기에 `custom_profile`이 루트와 같은 Telegram 봇 토큰을 써서 이게 났었다:

```plain text
telegram: state=fatal  error=telegram-bot-token_lock
  "Telegram bot token already in use (PID 93729). Stop the other gateway first."
```

- **원칙:** 프로필마다 그 플랫폼의 크리덴셜은 별도로 둔다.
- Slack이면 워크스페이스별로 다른 Slack 앱 + 다른 xapp/xoxb 쌍.
- 안 쓰는 플랫폼은 그 프로필 `.env`에서 토큰을 빼버린다 (우리는 `custom_profile`의 Telegram 토큰을 제거해서 락을 없앴다).
참고: `gateway_state.json`은 상태 전이 때만 갱신된다. 며칠 전 값이 그대로 남아 stale할 수 있으니, 현재 상태는 항상 로그로 교차 확인할 것.

### 7. 진단 레시피 (다음에 막히면 이 순서로)

```plain text
# 0) 게이트웨이가 몇 개, 어느 프로필로 떠 있나
ps aux | grep -E "hermes.*gateway" | grep -v grep

# 1) 해당 프로필 게이트웨이 상태
hermes -p <name> gateway status --deep

# 2) 실시간 에러 로그 (가장 정보량 많음)
tail -f ~/.hermes/profiles/<name>/logs/gateway.error.log
#   invalid_auth        → bot 토큰 무효 (4장)
#   *_lock / already in use → 토큰 공유 충돌 (6장)
#   channel_not_found   → HOME_CHANNEL/타깃 채널 ID 오류

# 3) 토큰 유효성 직접 검증 (읽기 전용)
curl -s -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $(grep ^SLACK_BOT_TOKEN ~/.hermes/profiles/<name>/.env | cut -d= -f2-)" \
  | python3 -m json.tool

# 4) .env 수정 시각 vs 프로세스 기동 시각 (재시작 필요 판단)
stat -f "%Sm  %N" ~/.hermes/profiles/<name>/.env
ps -o pid,lstart -p <gateway_pid>
```

토큰을 비교만 하고 싶을 땐(노출 없이) sha256 앞 8자리로 동일성만 확인:

```plain text
python3 -c "import hashlib,sys; print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:8])" "<token>"
```

### 8. 다음 프로필 만들 때 체크리스트

[ ] `hermes profile create <name>`
[ ] 새 워크스페이스마다 새 Slack 앱을 만든다 (기존 앱 재사용 X).
[ ] 그 앱에서 App-Level Token(`xapp`, `connections:write`) 발급 → `SLACK_APP_TOKEN`
[ ] 그 앱을 워크스페이스에 설치 후 Bot User OAuth Token(`xoxb`) 복사 → `SLACK_BOT_TOKEN`
[ ] `xapp`와 `xoxb`가 같은 앱의 것인지 확인 (섞이면 `invalid_auth`).
[ ] `SLACK_HOME_CHANNEL`, `SLACK_ALLOWED_USERS` 설정.
[ ] 다른 프로필과 토큰을 공유하지 않는다. 안 쓰는 플랫폼 토큰은 `.env`에서 제거.
[ ] `.env` 저장 → `auth.test`로 `ok:true` 먼저 확인 → 그 다음 게이트웨이 기동.
[ ] `.env`를 나중에 고쳤으면 → `gateway restart` (절대 `-all` 말고 `p <name>`).
[ ] `gateway.error.log`에 `invalid_auth` / `_lock`이 없는지 확인.
### 9. 부록

**프로필 디렉토리 구조**

```plain text
~/.hermes/                      # 루트(기본) 인스턴스 = HERMES_HOME
└── profiles/<name>/            # 프로필별 HERMES_HOME (완전 격리)
    ├── .env                    # API 키/토큰 (프로필 전용)
    ├── config.yaml             # 설정
    ├── state.db                # 세션 DB
    ├── gateway_state.json      # 게이트웨이 상태 스냅샷 (stale 주의)
    ├── gateway.pid / .lock     # 프로세스/락
    ├── channel_directory.json  # 수신 채널 목록 (실시간 갱신)
    ├── logs/                   # gateway.log, gateway.error.log, agent.log, errors.log
    ├── memories/ · skills/ · cron/ · sessions/
    └── SOUL.md                 # 페르소나 (비우면 기본 성격)
```

**명령어 레퍼런스**

```plain text
hermes profile create|list|switch|use|delete <name>
hermes -p <name> setup                 # 전체 설정 마법사
hermes -p <name> gateway setup         # 메신저 플랫폼 설정
hermes -p <name> gateway run [--replace] [-q]
hermes -p <name> gateway start|stop|restart [--all] [--system]
hermes -p <name> gateway status [--deep] [-l/--full]
```

![](image-02.png)

**한 줄 요약**

Socket Mode(`xapp`)는 붙는데 답장을 안 하면 십중팔구 `xoxb` 봇 토큰이 무효다. `auth.test`로 즉시 판별하고, `.env` 고쳤으면 게이트웨이 재시작을 잊지 말 것. 토큰은 프로필·워크스페이스마다 같은 앱에서 한 쌍씩, 절대 공유하지 말 것.

