#!/usr/bin/env python3
"""BLOG-011 Notion 원본 글에 쪽 커버(외부 https 주소)를 넣는다 — 기본은 dry-run.

Notion → Hugo 가져오기(src/property_mapper.py cover_from_page)가 쪽 커버의 외부 https 주소를 앞머리 cover로 옮긴다.
그림은 사이트 static/covers/ 에 있으므로 병합·배포로 주소가 살아난 뒤에 이 스크립트를 돌린다.

- 쓰는 것은 pages.update(cover=외부 주소) 하나뿐: 다른 속성·본문·지우기 0.
- 쪽 찾기 = DB 제목 칸 정확히 일치. 정확히 1쪽일 때만; 어느 하나라도 0쪽·2쪽 이상이면 아무것도 쓰지 않고 멈춤.
- 이미 같은 주소면 건너뜀(두 번 돌려도 같음). https 아닌 주소는 받지 않음.
- 실제로 쓰려면 --apply. 키: NOTION_TOKEN(Actions) 또는 NOTION_API_KEY. DB: --database 또는 NOTION_DATABASE_ID_POSTS.

    python scripts/set_notion_cover.py                      # 고정 표 세 쪽, dry-run
    python scripts/set_notion_cover.py --apply              # 고정 표 세 쪽에 씀
    python scripts/set_notion_cover.py --title "글 제목" --url https://gunn.kim/covers/x.jpg [--apply]
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://gunn.kim"

# 최근 글 5개 중 대표 이미지 없던 Notion 원본 세 쪽(D-20261109-03·04). 그림 = static/covers/<이름>.jpg
COVERS = [
    ("광군제 쇼핑, 영상을 다 보는 대신 AI 브라우저에게 출처를 따라가게 했다", f"{SITE}/covers/guanggunje.jpg"),
    ("GitHub Actions 60일 비활성화 함정과 Notion-Hugo 복구기", f"{SITE}/covers/github-actions-60day.jpg"),
    ("GitHub App Bootstrap을 자동화하며 만난 여섯 개의 함정", f"{SITE}/covers/github-app-bootstrap.jpg"),
]


def title_property(client, database_id):
    """DB의 제목(title) 칸 이름. 없으면 None"""
    body = client.databases.retrieve(database_id=database_id)
    for name, prop in body.get("properties", {}).items():
        if prop.get("type") == "title":
            return name
    return None


def find_pages(client, database_id, title_prop, title):
    found = client.databases.query(database_id=database_id,
                                   filter={"property": title_prop, "title": {"equals": title}})
    return [p for p in found.get("results", []) if not p.get("archived") and not p.get("in_trash")]


def current_cover(page):
    cover = page.get("cover") or {}
    return (cover.get(cover.get("type") or "") or {}).get("url")


def plan(client, database_id, pairs):
    """[(title, url, page | None, 찾은 수)] — 쓰기 전 전부 찾는다. DB에 제목 칸이 없으면 None"""
    title_prop = title_property(client, database_id)
    if not title_prop:
        return None
    rows = []
    for title, url in pairs:
        pages = find_pages(client, database_id, title_prop, title)
        rows.append((title, url, pages[0] if len(pages) == 1 else None, len(pages)))
    return rows


def main(argv=None, client=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database", default=os.environ.get("NOTION_DATABASE_ID_POSTS", ""))
    parser.add_argument("--title", help="이 제목 한 쪽만(--url 과 함께)")
    parser.add_argument("--url", help="넣을 커버 주소(https)")
    parser.add_argument("--apply", action="store_true", help="실제로 씀(없으면 dry-run)")
    args = parser.parse_args(argv)

    if bool(args.title) != bool(args.url):
        print("cover: --title 과 --url 은 함께", file=sys.stderr)
        return 2
    pairs = [(args.title, args.url)] if args.title else COVERS
    bad = [url for _, url in pairs if not url.strip().startswith("https://")]
    if bad:
        print(f"cover: https 주소만 — {bad}", file=sys.stderr)
        return 2
    pairs = [(title.strip(), url.strip()) for title, url in pairs]
    if not args.database:
        print("cover: DB id 없음(--database 또는 NOTION_DATABASE_ID_POSTS)", file=sys.stderr)
        return 2
    if client is None:
        token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
        if not token:
            print("cover: 키 없음(NOTION_TOKEN 또는 NOTION_API_KEY)", file=sys.stderr)
            return 2
        sys.path.insert(0, str(ROOT))
        from src.notion_retry import RetryingClient
        client = RetryingClient(auth=token)

    rows = plan(client, args.database, pairs)
    if rows is None:
        print("cover: DB에 제목 칸 없음 — 멈춤", file=sys.stderr)
        return 2
    for title, url, page, count in rows:
        print(f"cover: 찾음 {count}쪽 · {title} → {url}" + (f" (지금 {current_cover(page) or '없음'})" if page else ""))
    missing = [title for title, _, page, _ in rows if page is None]
    if missing:
        print(f"cover: 정확히 1쪽이 아닌 제목 {len(missing)}개 — 아무것도 쓰지 않고 멈춤", file=sys.stderr)
        return 1
    mode = "씀" if args.apply else "dry-run"
    for title, url, page, _ in rows:
        if current_cover(page) == url:
            print(f"cover: 같음(건너뜀) {page['id']} {title}")
            continue
        if args.apply:
            client.pages.update(page_id=page["id"], cover={"type": "external", "external": {"url": url}})
        print(f"cover: {mode} {page['id']} {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
