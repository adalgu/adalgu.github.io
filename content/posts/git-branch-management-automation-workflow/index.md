---
author: Gunn Kim
date: '2025-07-08'
description: 개발자라면 누구나 한 번쯤 Git 브랜치 이름을 어떻게 지을지 고민해 본 경험이 있을 겁니다. 단순한 브랜치 네이밍 고민에서
  시작해 팀 전체의 자동화 워크플로우까지 완성한 여정을 공유합니다.
draft: false
keywords: &id001
- Git
- 브랜치관리
- 자동화
- CI/CD
- 워크플로우
lastmod: '2025-07-17T05:46:00.000Z'
notion_id: 22a7522e-eb2f-8053-b935-d5de88d23583
slug: "git-branch-management-automation-workflow"
subtitle: 브랜치 네이밍 고민에서 시작된 팀 워크플로우 자동화 여정
summary: 개발자라면 누구나 한 번쯤 Git 브랜치 이름을 어떻게 지을지 고민해 본 경험이 있을 겁니다. 단순한 브랜치 네이밍 고민에서 시작해
  팀 전체의 자동화 워크플로우까지 완성한 여정을 공유합니다.
tags: *id001
title: Git 브랜치, 어떻게 관리해야 할까? - 개인의 기록에서 팀의 자동화까지
---

# Git 브랜치, 어떻게 관리해야 할까? - 개인의 기록에서 팀의 자동화까지

개발자라면 누구나 한 번쯤 Git 브랜치 이름을 어떻게 지을지 고민해 본 경험이 있을 겁니다. 단순히 `dev`, `feature`를 사용하는 것을 넘어, 더 체계적인 규칙을 만들고 싶다는 욕심이 생기기 마련이죠.

최근 저도 이런 고민에 빠졌습니다. 여러 LLM 모델을 다양한 개발 머신에서 테스트하는 상황에서, 작업 환경을 명확히 기록하고 싶다는 생각이 들었습니다.

> 나의 첫 아이디어:
"llm이름/개발머신이름-날짜 형식은 어떨까?"
예: gemini/macbook-20250708

이 아이디어는 '언제', '어떤 환경에서' 작업했는지 추적하기엔 더할 나위 없이 좋아 보였습니다. 하지만 이내 중요한 한 가지를 놓치고 있다는 것을 깨달았습니다. 바로 **'무엇을' 했는지**에 대한 정보가 빠져있다는 점입니다.

이 작은 질문에서 시작된 고민은 동료 AI들과의 협력적인 대화를 통해 점차 발전했고, 마침내 개인의 기록을 넘어 팀 전체의 생산성을 높이는 '자동화 워크플로우'라는 거대한 그림으로 완성되었습니다. 이 여정을 여러분과 함께 공유하고자 합니다.

### **기(起): 규칙의 시작, '목적'과 '환경'을 모두 담다**

저의 첫 아이디어는 '작업 내용'을 알기 어렵다는 명백한 단점이 있었습니다. 브랜치 이름만 보고서는 새로운 기능을 개발한 것인지, 버그를 수정한 것인지 알 수 없었죠.

이를 해결하기 위해 일반적인 브랜치 전략의 장점인 **'작업의 목적'**과 제 아이디어의 장점인 **'작업 환경'**을 결합한 하이브리드 전략이 탄생했습니다.

> [하이브리드 브랜치 전략]타입/환경/기능-설명

이 규칙에 따르면 브랜치는 다음과 같은 모습을 갖추게 됩니다.

- `feature/gemini-macbook/add-translation-api`
- `bugfix/claude-macmini/fix-login-error`
- `experiment/gpt4-macbook/test-new-prompt`
이제 브랜치 이름만 봐도 **"Gemini 모델을 맥북에서 작업했고, 번역 API 추가 기능을 개발했구나!"** 하고 명확하게 알 수 있게 되었습니다. 의도의 명확성과 환경의 추적성이라는 두 마리 토끼를 모두 잡은 셈입니다.

### **승(承): 규칙을 지키는 힘, '자동화'로 강제하기**

아무리 좋은 규칙이라도 지키지 않으면 무용지물입니다. 사람은 누구나 실수를 하기 마련이고, 바쁘다 보면 규칙을 잊어버리기도 합니다. 그래서 우리는 '시스템'의 힘을 빌리기로 했습니다.

규칙을 사람이 아닌, 기술이 검증하도록 만든 것입니다.

**1. 1차 방어선: 개인의 실수를 막는 Git Hooks**

개발자가 원격 저장소에 코드를 올리기(`push`) 전, 개인의 컴퓨터에서 브랜치 이름이 규칙에 맞는지 자동으로 검사하는 장치입니다. `.git/hooks/pre-push` 스크립트를 설정해두면, 규칙에 어긋나는 브랜치는 아예 푸시되지 않아 실수를 원천 봉쇄할 수 있습니다.

```plain text
#!/bin/bash

# 허용된 타입 목록
ALLOWED_TYPES="feature|bugfix|refactor|experiment|docs"
# 브랜치 네이밍 정규표현식 (타입/환경/설명#이슈번호 형식)
BRANCH_REGEX="^($ALLOWED_TYPES)\/([a-z0-9]+-[a-z0-9]+)\/([a-z0-9]+-)*[a-z0-9]+(#\d+)?$"

# 현재 푸시하려는 브랜치 이름 가져오기
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# main, dev 등 보호된 브랜치는 검사에서 제외
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "dev" ]]; then
    exit 0
fi

# 정규식 검사
if [[ ! "$CURRENT_BRANCH" =~ $BRANCH_REGEX ]]; then
    echo "[POLICY ERROR] 잘못된 브랜치 이름입니다."
    echo "규칙: 타입/llm-머신/기능-설명[#이슈번호]"
    echo "예시: feature/gemini-macbook/add-login-feature#123"
    exit 1 # Push 중단
fi

exit 0


```

**2. 2차 방어선: 팀의 규칙을 수호하는 CI/CD**

혹시 모를 예외(예: `git push --no-verify`)에 대비해, GitHub Actions와 같은 CI/CD 파이프라인에서 최종 검증을 수행합니다. Pull Request가 생성될 때마다 브랜치 이름을 검사하여, 규칙에 맞지 않으면 머지 자체를 막아버리는 강력한 수문장 역할을 합니다.

```plain text
# .github/workflows/branch-lint.yml
name: Branch Naming Convention
on:
  pull_request:
    types: [opened, edited, synchronize]

jobs:
  lint-branch-name:
    runs-on: ubuntu-latest
    steps:
      - name: Check Branch Name
        run: |
          BRANCH_NAME="${{ github.head_ref }}"
          REGEX="^(feature|bugfix|refactor|experiment|docs)\/([a-z0-9]+-[a-z0-9]+)\/([a-z0-9]+-)*[a-z0-9]+(#\d+)?$"
          if [[ ! "$BRANCH_NAME" =~ $REGEX ]]; then
            echo "::error::Branch name '${BRANCH_NAME}' does not follow the convention: 타입/llm-머신/기능-설명"
            exit 1
          fi


```

### **전(轉): 규칙의 활용, '생산성'을 폭발시키다**

이제 우리에겐 잘 구조화되고, 시스템에 의해 검증되는 브랜치 이름이 있습니다. 여기서 한 단계 더 나아가, 이 똑똑한 브랜치 이름을 **개발 생산성을 높이는 데 적극적으로 활용**하기 시작했습니다.

**1. 릴리스 노트 초안 자동 생성**

더 이상 수작업으로 릴리스 노트를 작성하지 않습니다. `main` 브랜치에 머지된 브랜치들의 `타입`과 `기능-설명`을 추출하여 릴리스 노트 초안을 자동으로 생성하는 스크립트를 만들었습니다.

- `feature/...` 브랜치는 '✨ 새로운 기능' 섹션에
- `bugfix/...` 브랜치는 '🐛 버그 수정' 섹션에
자동으로 분류되어 정리됩니다.

```plain text
#!/bin/bash
# generate_release_notes.sh
# 사용법: ./generate_release_notes.sh v1.2.0

VERSION=$1
OUTPUT_FILE="RELEASE_NOTES_${VERSION}.md"

echo "# Release ${VERSION}" > $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# 타입별로 머지된 PR 목록을 조회하여 추가
for TYPE in feature bugfix docs; do
  # 첫 글자를 대문자로 변경하여 헤더 생성
  HEADER="$(tr 'a-z' 'A-Z' <<< ${TYPE:0:1})${TYPE:1}s"
  echo "## ✨ ${HEADER}" >> $OUTPUT_FILE

  # GitHub CLI를 사용하여 해당 타입의 PR 목록을 가져와 포맷팅
  gh pr list --state merged --search "base:main" --json headRefName,title,number \
    | jq -r ".[] | select(.headRefName|startswith(\"${TYPE}/\")) | \"- [#\(.number)] \(.title)\"" >> $OUTPUT_FILE

  echo "" >> $OUTPUT_FILE
done

echo "릴리스 노트가 ${OUTPUT_FILE} 파일로 생성되었습니다."


```

**2. 똑똑한 CI/CD 파이프라인**

브랜치 `타입`에 따라 CI/CD 파이프라인이 동적으로 작동합니다. `docs/...` 브랜치는 불필요한 빌드나 테스트를 건너뛰고, `experiment/...` 브랜치는 자동으로 테스트 서버에 배포되어 빠르게 결과를 확인할 수 있습니다.

### **결(結): 궁극의 워크플로우를 향하여**

우리의 여정은 여기서 멈추지 않았습니다. 잘 짜인 브랜치 규칙과 더불어, **Conventional Commits**라는 커밋 메시지 규칙을 도입했습니다. 그리고 이 모든 것을 `semantic-release`라는 강력한 자동화 도구와 결합했습니다.

그 결과, 다음과 같은 꿈의 워크플로우가 완성되었습니다.

1. 개발자는 `feat: add user profile`과 같은 규칙에 맞춰 커밋하고 `main` 브랜치에 코드를 머지합니다.
1. CI/CD 파이프라인이 이를 감지하고 `semantic-release`를 실행합니다.
1. `semantic-release`는 커밋 메시지를 분석하여 **다음 버전을 자동으로 결정**합니다. (`feat`이므로 Minor 버전 상승!)
1. `CHANGELOG.md` 파일을 **자동으로 업데이트**합니다.
1. 결정된 버전으로 Git 태그를 생성하고, 변경 내역과 함께 **GitHub Release 페이지를 자동으로 발행**합니다.
1. 마지막으로, 새로운 버전이 릴리스되었다는 **알림을 팀 Slack 채널에 자동으로 전송**합니다.
이 모든 과정은 아래와 같은 간단한 워크플로우 파일 하나로 설정됩니다.

```plain text
# .github/workflows/release.yml
name: Semantic Release
on:
  push:
    branches:
      - main
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run semantic-release
        run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # NPM에 배포할 경우 NPM_TOKEN도 필요
          # NPM_TOKEN: ${{ secrets.NPM_TOKEN }}


```

단순한 브랜치 네이밍 고민에서 시작된 이 여정은, 결국 개발자가 코드에만 집중할 수 있도록 돕는 완전 자동화된 배포 파이프라인 구축으로 이어졌습니다.

좋은 브랜치 전략은 단순히 코드를 정리하는 것을 넘어, 팀의 협업 방식을 바꾸고 개발 워크플로우 전체를 혁신하는 강력한 첫걸음이 될 수 있습니다. 여러분도 오늘, 팀의 브랜치 전략을 한번 점검해 보는 것은 어떨까요?


## 📋 현재 상황에 맞는 단계별 명령어

### 1️⃣ 현재 상태 확인 및 메인 동기화

```shell
# 현재 브랜치와 상태 확인
git status
git branch -a

# 메인 브랜치로 이동
git checkout main
# 또는
git switch main

# 원격 저장소에서 최신 변경사항 가져오기
git pull origin main

```

### 2️⃣ 새 브랜치 생성 (문서의 네이밍 규칙 적용)

```shell
# 브랜치 생성 및 이동 (문서 규칙: 타입/환경/기능-설명)
git checkout -b feature/맥북환경/기능이름-설명
# 예시:
git checkout -b feature/macbook/add-user-profile
git checkout -b bugfix/macbook/fix-login-error
git checkout -b experiment/gpt4-macbook/test-new-prompt

# 또는 최신 Git 버전
git switch -c feature/macbook/add-user-profile

```

## 🔄 주요 워크플로우별 명령어 모음

### **A. 새 기능 개발 워크플로우**

```shell
# 1. 최신 메인에서 시작
git checkout main && git pull origin main

# 2. 새 브랜치 생성
git checkout -b feature/macbook/기능명-설명

# 3. 작업 후 커밋 (Conventional Commits 규칙 적용)
git add .
git commit -m "feat: 새로운 기능 추가 설명"

# 4. 원격에 푸시
git push origin feature/macbook/기능명-설명

# 5. PR 생성 (GitHub CLI 사용시)
gh pr create --title "feat: 새로운 기능 추가" --body "기능 설명"

```

### **B. 버그 수정 워크플로우**

```shell
# 1. 최신 메인에서 시작
git checkout main && git pull origin main

# 2. 버그 수정 브랜치 생성
git checkout -b bugfix/macbook/fix-버그설명

# 3. 수정 후 커밋
git add .
git commit -m "fix: 버그 수정 내용"

# 4. 푸시 및 PR
git push origin bugfix/macbook/fix-버그설명
gh pr create --title "fix: 버그 수정" --body "수정 내용"

```

### **C. 실험적 작업 워크플로우**

```shell
# 1. 실험 브랜치 생성
git checkout -b experiment/macbook/test-새로운시도

# 2. 실험 후 커밋
git commit -m "feat: 실험적 기능 테스트"

# 3. 푸시 (문서에 따르면 자동으로 테스트 서버 배포됨)
git push origin experiment/macbook/test-새로운시도

```

## ⚙️ 문서의 자동화 규칙 적용을 위한 설정

### **1. Git Hooks 설정 (브랜치 이름 검증)**

```shell
# .git/hooks/pre-push 파일 생성
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
ALLOWED_TYPES="feature|bugfix|refactor|experiment|docs"
BRANCH_REGEX="^($ALLOWED_TYPES)\/([a-z0-9]+-[a-z0-9]+)\/([a-z0-9]+-)*[a-z0-9]+(#\d+)?$"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "dev" ]]; then
    exit 0
fi

if [[ ! "$CURRENT_BRANCH" =~ $BRANCH_REGEX ]]; then
    echo "[POLICY ERROR] 잘못된 브랜치 이름입니다."
    echo "규칙: 타입/환경/기능-설명"
    echo "예시: feature/macbook/add-login-feature"
    exit 1
fi
exit 0
EOF

# 실행 권한 부여
chmod +x .git/hooks/pre-push

```

### **2. Conventional Commits 규칙**

```shell
# 커밋 메시지 규칙
git commit -m "feat: 새로운 기능 추가"     # 새 기능
git commit -m "fix: 버그 수정"           # 버그 수정
git commit -m "docs: 문서 업데이트"       # 문서
git commit -m "style: 코드 스타일 수정"    # 스타일
git commit -m "refactor: 코드 리팩토링"   # 리팩토링
git commit -m "test: 테스트 추가"        # 테스트
git commit -m "chore: 기타 작업"         # 기타

```

## 🚀 일상적으로 자주 쓸 명령어 조합

### **매일 작업 시작할 때**

```shell
# 원격 변경사항 확인 및 동기화
git checkout main
git pull origin main
git branch -d 완료된브랜치명  # 로컬에서 완료된 브랜치 정리

```

### **작업 완료 후 정리**

```shell
# PR 머지 후 정리
git checkout main
git pull origin main
git branch -d feature/macbook/완료된기능명  # 로컬 브랜치 삭제
git remote prune origin  # 원격에서 삭제된 브랜치 정리

```

### **긴급 버그 수정**

```shell
# 핫픽스 워크플로우
git checkout main
git pull origin main
git checkout -b bugfix/macbook/hotfix-심각한버그
# 수정 작업
git add . && git commit -m "fix: 심각한 버그 긴급 수정"
git push origin bugfix/macbook/hotfix-심각한버그
gh pr create --title "🚨 긴급 버그 수정" --body "심각한 버그 수정"

```

이제 문서에서 제안하는 체계적인 브랜치 관리 전략을 실제로 적용할 수 있습니다! 브랜치 이름만 봐도 **"어떤 환경에서, 무엇을, 왜"** 작업했는지 명확하게 알 수 있게 됩니다.

