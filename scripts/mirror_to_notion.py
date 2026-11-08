#!/usr/bin/env python3
"""BL-003 Hugo → Notion 거울.

저장소 손글 묶음(content/posts/<slug>/index.md)이 원본이고, Notion 블로그 DB는 배포 뒤 받아 가는 거울이다.
`draft: false` 묶음마다 Slug로 DB 쪽을 찾아 없으면 만들고, 있으면 속성을 고친다(같은 글 두 번 = 쪽 1개).

- 거울 쪽은 늘 Source = hugo · skipRendering = 켬 → Notion → Hugo 가져오기가 건너뛴다(손글 덮기 0).
- 같은 Slug라도 Source = hugo 가 아닌 쪽(Notion에서 쓴 옛 글)은 건드리지 않고 경고만 낸다.
- Notion 쪽 지우기 0. 본문 갈아끼우기(옛 블록 지우기)는 --replace-body 를 줄 때만.
- 키: NOTION_TOKEN(Actions) 또는 NOTION_API_KEY. DB: --database 또는 NOTION_DATABASE_ID_POSTS.

    python scripts/mirror_to_notion.py --dry-run
    python scripts/mirror_to_notion.py --only bl003-hugo-first-test --test   # 초안도 거울로(isPublished 끔)
"""
import argparse
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEXT_LIMIT = 2000      # Notion rich_text 한 칸 글자 한도
APPEND_LIMIT = 100     # 한 번에 붙일 수 있는 블록 수
CLEAR_ROUNDS = 3       # 옛 본문 지우기: 다시 읽어 남은 게 있으면 이만큼까지 되풀이


# ---------- 손글 읽기 ----------

def read_bundle(path):
    """index.md → (앞머리 dict, 본문 str). 앞머리 없으면 None"""
    raw = Path(path).read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return None
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None
    meta = yaml.safe_load(parts[1]) or {}
    return meta, parts[2].lstrip("\n")


def find_posts(posts_dir, only=(), include_drafts=False):
    posts = []
    for index in sorted(Path(posts_dir).glob("*/index.md")):
        parsed = read_bundle(index)
        if not parsed:
            continue
        meta, body = parsed
        slug = str(meta.get("slug") or index.parent.name)
        if only and slug not in only:
            continue
        if meta.get("draft", False) and not include_drafts:
            continue
        posts.append({"slug": slug, "meta": meta, "body": body, "path": str(index)})
    return posts


# ---------- Markdown → Notion 블록 ----------

INLINE = re.compile(r"\*\*(.+?)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)")


def rich_text(text):
    out = []

    def push(content, bold=False, code=False, link=None):
        for at in range(0, len(content), TEXT_LIMIT):
            item = {"type": "text", "text": {"content": content[at:at + TEXT_LIMIT]}}
            if link:
                item["text"]["link"] = {"url": link}
            if bold or code:
                item["annotations"] = {"bold": bold, "code": code}
            out.append(item)

    pos = 0
    for match in INLINE.finditer(text):
        if match.start() > pos:
            push(text[pos:match.start()])
        bold, code, label, url = match.groups()
        if bold is not None:
            push(bold, bold=True)
        elif code is not None:
            push(code, code=True)
        else:
            push(label, link=url)
        pos = match.end()
    if pos < len(text):
        push(text[pos:])
    return out


def block(kind, text):
    return {"object": "block", "type": kind, kind: {"rich_text": rich_text(text)}}


def markdown_blocks(markdown):
    blocks, para, lines = [], [], markdown.splitlines()

    def flush():
        if para:
            blocks.append(block("paragraph", " ".join(para)))
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            blocks.append({"object": "block", "type": "code",
                           "code": {"rich_text": [{"type": "text", "text": {"content": c}}
                                                  for c in _chunks("\n".join(code))],
                                    "language": "plain text"}})
        elif not stripped:
            flush()
        elif m := re.match(r"(#{1,3})\s+(.*)", stripped):
            flush()
            blocks.append(block(f"heading_{len(m.group(1))}", m.group(2)))
        elif re.fullmatch(r"(-{3,}|\*{3,})", stripped):
            flush()
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif m := re.match(r"[-*+]\s+(.*)", stripped):
            flush()
            blocks.append(block("bulleted_list_item", m.group(1)))
        elif m := re.match(r"\d+[.)]\s+(.*)", stripped):
            flush()
            blocks.append(block("numbered_list_item", m.group(1)))
        elif stripped.startswith(">"):
            flush()
            blocks.append(block("quote", stripped.lstrip(">").strip()))
        else:
            para.append(stripped)
        i += 1
    flush()
    return blocks


def _chunks(text):
    return [text[at:at + TEXT_LIMIT] for at in range(0, len(text), TEXT_LIMIT)] or [""]


# ---------- Notion 쪽 ----------

def _as_list(value):
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def page_properties(post, schema, test=False):
    """DB에 있는 칸만 채운다(없는 칸을 보내면 Notion이 400)."""
    meta = post["meta"]
    props = {
        "Name": {"title": rich_text(str(meta.get("title") or post["slug"]))},
        "Slug": {"rich_text": rich_text(post["slug"])},
        "skipRendering": {"checkbox": True},
        "isPublished": {"checkbox": not test},
    }
    if meta.get("date"):
        props["Date"] = {"date": {"start": str(meta["date"]).replace(" ", "T")}}
    if meta.get("description"):
        props["Description"] = {"rich_text": rich_text(str(meta["description"]))}
    tags = [str(t).replace(",", " ") for t in _as_list(meta.get("tags"))]
    if tags:
        props["Tags"] = {"multi_select": [{"name": t} for t in tags]}
    categories = _as_list(meta.get("categories"))
    if categories:
        props["Category"] = {"select": {"name": str(categories[0]).replace(",", " ")}}
    source_type = schema.get("Source")
    if source_type == "select":
        props["Source"] = {"select": {"name": "hugo"}}
    elif source_type == "rich_text":
        props["Source"] = {"rich_text": rich_text("hugo")}
    return {name: value for name, value in props.items() if name in schema}


def _plain(prop):
    if not prop:
        return ""
    kind = prop.get("type")
    if kind == "select":
        return (prop.get("select") or {}).get("name", "")
    if kind in ("rich_text", "title"):
        return "".join(t.get("plain_text") or t.get("text", {}).get("content", "") for t in prop.get(kind, []))
    return ""


def is_mirror(page):
    return _plain(page.get("properties", {}).get("Source")).strip().lower() == "hugo"


def mirror_post(client, database_id, schema, post, test=False, replace_body=False, allow_no_source=False, dry_run=False):
    """한 글 → ('create'|'update'|'skip', page_id 또는 이유)"""
    found = client.databases.query(database_id=database_id,
                                   filter={"property": "Slug", "rich_text": {"equals": post["slug"]}})
    pages = found.get("results", [])
    ours = [p for p in pages if is_mirror(p) or (allow_no_source and "Source" not in schema)]
    if pages and not ours:
        return "skip", f"slug {post['slug']}: Source=hugo 아닌 Notion 쪽이 이미 있음 — 건드리지 않음"
    props = page_properties(post, schema, test=test)
    children = markdown_blocks(post["body"])
    if dry_run:
        return ("update" if ours else "create"), "dry-run"
    if not ours:
        created = client.pages.create(parent={"database_id": database_id}, properties=props,
                                      children=children[:APPEND_LIMIT])
        _append(client, created["id"], children[APPEND_LIMIT:])
        return "create", created["id"]
    page_id = ours[0]["id"]
    client.pages.update(page_id=page_id, properties=props)
    if replace_body:
        _clear_children(client, page_id)
        _append(client, page_id, children)
    return "update", page_id


def _child_ids(client, page_id):
    """쪽의 모든 자식 블록 id — 한 번에 100개씩이라 has_more/next_cursor 끝까지 읽는다."""
    ids, cursor = [], None
    while True:
        kwargs = {"block_id": page_id, "page_size": APPEND_LIMIT}
        if cursor:
            kwargs["start_cursor"] = cursor
        body = client.blocks.children.list(**kwargs)
        ids += [item["id"] for item in body.get("results", [])]
        cursor = body.get("next_cursor")
        if not body.get("has_more") or not cursor:
            return ids


def _clear_children(client, page_id, rounds=CLEAR_ROUNDS):
    """옛 본문 블록 전부 지움. 다 모은 뒤 지우고(지우며 넘기면 커서가 어긋남) 다시 읽어 0개일 때까지.
    BLOG-011 보탬 1: 첫 100개만 지워 103블록 쪽에 옛 3블록이 맨 앞에 남던 것."""
    for _ in range(rounds):
        ids = _child_ids(client, page_id)
        if not ids:
            return
        for block_id in ids:
            client.blocks.delete(block_id=block_id)
    raise RuntimeError(f"mirror: {page_id} 옛 본문이 {rounds}번 지운 뒤에도 남음 — 새 본문 붙이지 않고 멈춤")


def _append(client, page_id, children):
    for at in range(0, len(children), APPEND_LIMIT):
        client.blocks.children.append(block_id=page_id, children=children[at:at + APPEND_LIMIT])


def database_schema(client, database_id):
    body = client.databases.retrieve(database_id=database_id)
    return {name: prop.get("type") for name, prop in body.get("properties", {}).items()}


def main(argv=None, client=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--posts-dir", default=str(ROOT / "content" / "posts"))
    parser.add_argument("--database", default=os.environ.get("NOTION_DATABASE_ID_POSTS", ""))
    parser.add_argument("--only", action="append", default=[], help="이 slug만(여러 번 가능)")
    parser.add_argument("--test", action="store_true", help="초안도 거울로, isPublished 끔(시험 쪽)")
    parser.add_argument("--replace-body", action="store_true", help="있는 쪽 본문 블록을 지우고 다시 씀")
    parser.add_argument("--allow-no-source-column", action="store_true",
                        help="DB에 Source 칸이 없을 때 Slug만으로 거울 쪽을 찾음(시험 전용)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    posts = find_posts(args.posts_dir, only=set(args.only), include_drafts=args.test)
    if not posts:
        print("mirror: 거울로 보낼 글 없음")
        return 0
    if not args.database:
        print("mirror: DB id 없음(--database 또는 NOTION_DATABASE_ID_POSTS)", file=sys.stderr)
        return 2
    if client is None:
        token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
        if not token:
            print("mirror: 키 없음(NOTION_TOKEN 또는 NOTION_API_KEY)", file=sys.stderr)
            return 2
        sys.path.insert(0, str(ROOT))
        from src.notion_retry import RetryingClient
        client = RetryingClient(auth=token)

    schema = database_schema(client, args.database)
    if "Source" not in schema and not args.allow_no_source_column:
        print("mirror: DB에 Source 칸 없음 — 거울을 가려낼 수 없어 멈춤(칸 추가는 승인 건)", file=sys.stderr)
        return 2
    failed = 0
    for post in posts:
        action, detail = mirror_post(client, args.database, schema, post, test=args.test,
                                     replace_body=args.replace_body,
                                     allow_no_source=args.allow_no_source_column, dry_run=args.dry_run)
        print(f"mirror: {action} {post['slug']} {detail}")
        failed += action == "skip"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
