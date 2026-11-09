#!/usr/bin/env python3
"""BLOG-018 step 1: published Hugo posts without a cover, newest first (slot r7-P05).

    python scripts/list_missing_covers.py [--limit 10] [--posts content/posts] [--json]

A post is missing a cover when its front matter has no `cover.image` (or no `cover` at all). Drafts are left out.
Reads bundle files only: no writes, no network, no Notion lookups. Every row is a repo bundle (kind Hugo); the
notion_id column only says whether a moved Notion page exists, so the round can check its original cover by hand.
Exit 0 always when the folder exists (an empty list is a fine answer), 2 when it does not.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.ssot.bundle import all_bundles  # noqa: E402  the same bundle reader the sync engine uses


def cover_image(meta):
    cover = meta.get("cover")
    if isinstance(cover, dict):
        return str(cover.get("image") or "").strip()
    return str(cover or "").strip()


def is_draft(meta):
    return meta.get("draft") is True or str(meta.get("draft")).strip().lower() == "true"


def missing(posts_dir):
    rows = []
    for bundle in all_bundles(posts_dir):
        meta = bundle.meta
        if is_draft(meta) or cover_image(meta):
            continue
        rows.append({"slug": bundle.slug, "date": str(meta.get("date") or "")[:10], "kind": "Hugo",
                     "title": str(meta.get("title") or "").strip(), "notion_id": bool(meta.get("notion_id"))})
    return sorted(rows, key=lambda r: (r["date"], r["slug"]), reverse=True)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="list_missing_covers")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--posts", default=str(ROOT / "content" / "posts"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not Path(args.posts).is_dir():
        print(f"list_missing_covers: no folder {args.posts}", file=sys.stderr)
        return 2
    rows = missing(args.posts)
    shown = rows[:max(args.limit, 0)]
    if args.json:
        print(json.dumps({"total": len(rows), "rows": shown}, ensure_ascii=False, indent=2))
        return 0
    print(f"| # | date | slug | kind | notion_id |  — {len(shown)} of {len(rows)} without a cover")
    print("|---|---|---|---|---|")
    for number, row in enumerate(shown, 1):
        print(f"| {number} | {row['date']} | {row['slug']} | {row['kind']} | {'yes' if row['notion_id'] else 'no'} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
