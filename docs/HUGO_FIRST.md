# Hugo 원본 흐름 (BL-003)

> **Superseded (BLOG-017)**: the repo is now the only source and Notion a synced mirror. See [REPO_SSOT.md](REPO_SSOT.md).
> The cache restore (`restore_hand_posts.sh`) and the flat-post gate (`check_flat_posts.sh`) below were removed with the old import.

새 글은 **저장소 Markdown이 원본**이다. Notion 블로그 DB는 배포 뒤 받아 가는 거울이다.
옛 글(Notion에서 쓴 글)과 Notion → Hugo 가져오기는 그대로 돈다.

| | 옛 흐름 | 새 흐름 |
|---|---|---|
| 원본 | Notion 쪽 | `content/posts/<slug>/index.md` (git 추적) |
| 초안 | `isPublished` 끔 | `draft: true` |
| 공개 | `isPublished` 켬 → 매시간 동기화 | PR 병합(main 푸시) — **지휘관 승인 건** |
| Notion | 원본 | 거울(`Source = hugo`, `skipRendering` 켬) |

## 새 글 쓰기

```bash
mkdir -p content/posts/my-slug
$EDITOR content/posts/my-slug/index.md
```

```yaml
---
title: "제목"
date: 2026-11-01T09:00:00+09:00   # 지금보다 뒤면 빌드에서 빠진다(buildFuture 꺼짐)
slug: my-slug                     # 주소 = /posts/my-slug/, 거울도 이 값으로 찾는다
description: "한 줄 요약"          # 테마가 제목 아래 그린다 (subtitle 은 안 그림)
tags: ["태그"]
categories: ["분류"]
draft: true
---
```

- **`id:` 를 쓰지 않는다.** full-sync 고아 정리가 앞머리 `id` 로 지울 파일을 고른다(`id` 없는 파일은 건너뜀).
- 그림은 같은 묶음 폴더에 둔다(`content/posts/my-slug/cover.png`) — 묶음 폴더 전체가 추적된다.
- `content/posts/*.md`(평평한 파일)는 Notion에서 가져온 글 자리라 gitignore다. 손글은 꼭 폴더(묶음)로.

## 미리보기

```bash
hugo server -D --bind 0.0.0.0 --baseURL "http://$(ipconfig getifaddr en0):1313/"
# 폰(같은 와이파이)에서 http://<맥 IP>:1313/posts/my-slug/  — 다 보면 Ctrl+C
```

`hugo -D` 는 초안을 넣고, 배포 빌드(`hugo --minify`)는 넣지 않는다.
밖에서 열리는 미리보기 주소(Cloudflare Pages 미리보기 프로젝트 등)는 새 프로젝트·새 키가 필요해 아직 없다.

## 공개

1. 가지에서 글을 쓰고 PR(main 대상)을 연다. 초안이면 `draft: true` 그대로.
2. 공개할 때 `draft: false` 로 바꾼 커밋을 PR에 올리고, **지휘관 승인 뒤 병합**.
3. main 푸시 → 기존 워크플로(`notion-hugo-deploy.yml`)가 빌드·배포. 이때 손글은 캐시 판이 아니라 커밋 판으로 빌드된다(`scripts/restore_hand_posts.sh`).

## Notion 거울

- `mirror` 잡: 배포 뒤 `scripts/mirror_to_notion.py` 가 `draft: false` 묶음마다 `Slug` 로 Notion 쪽을 찾아 없으면 만들고 있으면 속성을 고친다. 같은 글을 여러 번 돌려도 쪽은 1개.
- 거울 쪽은 늘 `Source = hugo`·`skipRendering` 켬 → 가져오기가 건너뛴다(손글 덮기 0). 같은 Slug의 옛 Notion 쪽(Source ≠ hugo)은 건드리지 않고 잡이 실패로 알린다.
- Notion 쪽 지우기 0. 본문 갈아끼우기는 `--replace-body` 를 줄 때만(그 쪽의 옛 블록을 지움).
- **스위치**: 저장소 변수 `NOTION_MIRROR=on` 일 때만 돈다(기본 꺼짐). 켜기 전에 필요한 것:
  1. Notion 블로그 DB에 `Source` 칸(select, 값 `hugo`) 추가
  2. Actions 비밀값 `NOTION_TOKEN` 의 통합이 그 DB에 쓰기 권한이 있는지 확인
- 손으로 돌리기: `python scripts/mirror_to_notion.py --dry-run` (키: `NOTION_TOKEN` 또는 `NOTION_API_KEY`, DB: `NOTION_DATABASE_ID_POSTS`).

## 되돌리기

- 한 줄: `git revert <BL-003 커밋>` → main 푸시. 워크플로·gitignore·가져오기 건너뜀이 옛 판으로 돌아간다.
- 옛 흐름으로 돌아가는 법: Notion에서 쓰고 `isPublished` 를 켠다(지금도 그대로 됨). 거울 쪽은 `skipRendering` 이 켜져 있어 되돌린 뒤에도 사이트에 겹쳐 나오지 않는다. 손글을 Notion 원본으로 옮기려면 그 거울 쪽의 `Source` 를 비우고 `skipRendering` 을 끈 뒤 저장소 묶음을 지운다.
- 거울만 끄기: 저장소 변수 `NOTION_MIRROR` 를 지우거나 `off`.
