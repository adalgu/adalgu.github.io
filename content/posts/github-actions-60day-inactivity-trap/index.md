---
author: Gunn Kim
date: '2026-09-06'
description: 정기 cron 스케줄로 돌던 블로그 배포 워크플로우가 왜 조용히 멈췄을까? GitHub의 60일 비활성화 정책(disabled_inactivity)
  분석과 복구기
draft: false
keywords: &id001
- GitHub Actions
- Hugo
- Notion
- Automation
- CI/CD
lastmod: '2026-09-06T16:56:00.000Z'
notion_id: 3d37522e-eb2f-81fa-aa32-e5b8aed5c366
slug: "github-actions-60day-inactivity-trap"
subtitle: ''
summary: 정기 cron 스케줄로 돌던 블로그 배포 워크플로우가 왜 조용히 멈췄을까? GitHub의 60일 비활성화 정책(disabled_inactivity)
  분석과 복구기
tags: *id001
title: GitHub Actions 60일 비활성화 함정과 Notion-Hugo 복구기
---

## 1. 발단: 노션에 글을 썼는데 왜 배포가 안 될까?

내 개인 기술 블로그([gunn.kim](https://gunn.kim))는 **Notion을 Headless CMS로 사용하고, GitHub Actions가 매시간 정각(`0 * * * *`)마다 Notion 데이터베이스의 글을 읽어와 Hugo(PaperMod)로 빌드한 뒤 GitHub Pages로 배포**하는 완전 자동화 파이프라인을 갖추고 있다.

그런데 최근 새 글을 작성하고 `isPublished: true`를 켰음에도 불구하고, 몇 시간이 지나도 웹사이트에 글이 반영되지 않는 현상이 발생했다.

로컬에서 수동으로 빌드한 것도 아니고, 노션 API 키가 만료된 것도 아니었다. 도대체 무엇이 문제였을까?

---

## 2. 진단: 침묵의 살인자 `disabled_inactivity`

GitHub 저장소의 Actions 탭과 GitHub CLI(`gh`)를 통해 워크플로우 상태를 추적했다.

```bash
gh workflow list --repo adalgu/adalgu.github.io
```

출력 결과는 충격적이었다:

```plain text
Notion → Hugo → GitHub Pages  disabled_inactivity  5293739
```

상태가 `active`가 아니라 **`disabled_inactivity`**로 잠겨 있었다!

### GitHub Actions의 숨겨진 정책

GitHub 공식 문서에 따르면:

> **Public/Private 저장소에서 60일 동안 커밋이나 활동이 없는 경우, 비용 및 컴퓨팅 자원 낭비를 방지하기 위해 스케줄된 워크플로우(`schedule` cron)를 자동으로 비활성화한다.**

마지막 커밋이 2026년 5월경이었고, 이후 60일 동안 저장소 자체에 Git 커밋이 발생하지 않았다.

노션에서 아무리 글을 새로 쓰고 수정을 해도, 그것은 'GitHub 저장소 내부의 Git 커밋'이 아니기 때문에 GitHub 시스템은 이 레포지토리를 **"방치된 유휴 저장소"**로 판단하여 스케줄러를 차단해 버린 것이다.

---

## 3. 해결: 즉각적인 복구 및 트리거

원인을 알았으니 해결은 명확했다. GitHub CLI를 통해 워크플로우를 즉시 다시 켜고 수동 트리거를 걸었다.

```bash
# 1. 비활성화된 워크플로우 재활성화
gh workflow enable notion-hugo-deploy.yml --repo adalgu/adalgu.github.io

# 2. 즉시 빌드 트리거
gh workflow run notion-hugo-deploy.yml --repo adalgu/adalgu.github.io
```

약 1분 27초 후, GitHub Actions가 Notion API를 호출하여 최신 글을 가져오고, Hugo 빌드를 성공적으로 마친 뒤 GitHub Pages에 정상 배포(HTTP 200)되었다.

```markdown
graph TD
    A[Notion Database: Blog Posts] -->|1. isPublished: true| B(GitHub Actions Runner)
    B -->|2. notion_hugo_app.py| C[Markdown Files in content/posts]
    C -->|3. hugo --minify| D[Public HTML Assets]
    D -->|4. deploy-pages| E[GitHub Pages: adalgu.github.io]
    E -->|5. Cloudflare CDN CNAME| F[Final: https://gunn.kim]
```

---

## 4. 구조적 개선: 무엇을 배웠는가?

이번 트러블슈팅을 통해 얻은 세 가지 핵심 교훈은 다음과 같다:

1. **외부 CMS와 Git 스케줄러의 비대칭성**:

- 외부(Notion)에서만 데이터를 업데이트하면 GitHub 입장에선 저장소가 유휴 상태로 보여 스케줄러가 잠긴다.
- 따라서 **Git 커밋을 글의 단일 진실 공급원(SSOT)으로 삼거나**, 정기적인 커밋 핑(keep-alive) 워크플로우를 함께 두어야 한다.
2. **원클릭 배포 CLI 구축**:

- 1시간 주기를 마냥 기다리지 않고 터미널에서 즉시 반영할 수 있는 로컬 글로벌 명령어 `gunn-publish`를 구축했다:
```bash
     gunn-publish
```

3. **자율 모니터링의 필요성**:

- 파이프라인이 멈췄을 때 사람이 나중에 알아차리는 것이 아니라, 에이전트나 cron 워크플로우가 `disabled_inactivity` 상태를 주기적으로 감시하고 알림을 주는 감시 레이어가 필수적이다.
자동화는 한 번 구축했다고 끝나는 것이 아니라, 플랫폼 제공자의 정책 변화와 침묵의 실패(Silent Failure)를 끊임없이 모니터링해야 비로소 완성된다.

