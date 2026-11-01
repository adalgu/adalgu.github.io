#!/usr/bin/env bash
# BLOG-010: '글 없음' 막이. Notion에서 가져온 평평한 글(content/posts/*.md)의 수를 센다.
# 손글 묶음(content/posts/<slug>/index.md)은 세지 않는다 — 묶음이 늘 있어 옛 막이(find -name '*.md')는 동기화가 0개여도 통과했다.
# - 0개 → 실패(exit 1)
# - 직전 성공 수(기준 파일)의 RATIO% 미만 → 실패(exit 1). 기준 파일 없음 = 처음 판 → 0만 막는다.
# - 통과하면 기준 파일에 이번 수를 적는다(캐시에 실려 다음 실행이 읽음 — 캐시는 job 성공 때만 저장되므로 실패한 실행의 수는 남지 않는다).
# 쓰기: scripts/check_flat_posts.sh [글 폴더] [기준 파일] [RATIO]   (기본: content/posts .notion-hugo-flat-count 50)
set -euo pipefail
POSTS_DIR="${1:-content/posts}"
BASELINE_FILE="${2:-.notion-hugo-flat-count}"
RATIO="${3:-50}"

count=0
if [ -d "$POSTS_DIR" ]; then
  count=$(find "$POSTS_DIR" -maxdepth 1 -type f -name '*.md' ! -name '_index.md' | wc -l | tr -d ' ')
fi

if [ "$count" -eq 0 ]; then
  echo "❌ Notion 평평한 글 0개 — API 동기화 실패 가능(손글 묶음만 있는 사이트는 배포하지 않음)" >&2
  exit 1
fi

if [ -f "$BASELINE_FILE" ]; then
  baseline=$(tr -dc '0-9' < "$BASELINE_FILE")
  if [ -n "$baseline" ] && [ "$baseline" -gt 0 ] && [ $((count * 100)) -lt $((baseline * RATIO)) ]; then
    echo "❌ Notion 평평한 글 ${count}개 — 직전 성공 ${baseline}개의 ${RATIO}% 미만, 배포 멈춤" >&2
    exit 1
  fi
fi

echo "$count" > "$BASELINE_FILE"
echo "✅ Notion 평평한 글 ${count}개 (기준 파일 갱신)"
