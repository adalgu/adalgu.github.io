#!/usr/bin/env bash
# BL-003: 캐시 복원(actions/cache, content/posts/) 뒤에 손글 묶음을 저장소 판으로 되돌린다.
# - 추적 중인 content/posts/<slug>/ 파일 = 이번 커밋 판으로 다시 깔기(캐시 옛 판 덮어쓰기 막기)
# - 추적하지 않는 묶음(저장소에서 지운 손글이 캐시에만 남은 것) = 지우기
# - Notion에서 가져온 평평한 글(content/posts/*.md)은 gitignore라 그대로 둔다
set -euo pipefail
# 로컬에서 돌리면 커밋 안 한 손글이 지워진다 — CI 밖에서는 --local 을 줘야만 돈다
if [ -z "${CI:-}" ] && [ "${1:-}" != "--local" ]; then
  echo "restore_hand_posts.sh: CI 전용(커밋 안 한 손글을 지움). 로컬 시험은 --local" >&2
  exit 2
fi
cd "$(git rev-parse --show-toplevel)"
if git ls-files --error-unmatch content/posts >/dev/null 2>&1; then
  git checkout -- content/posts
fi
git clean -fdq -- content/posts
echo "hand posts restored: $(git ls-files content/posts | wc -l | tr -d ' ') tracked file(s)"
