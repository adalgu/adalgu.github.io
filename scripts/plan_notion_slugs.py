#!/usr/bin/env python3
"""BLOG-017 addendum 5: plan (dry run by default) the Notion Slug column = bundle folder name.

Bundles are tied to their Notion page by front matter notion_id; the engine writes Slug = folder on its next
push of that bundle anyway. This lists, read-only, which pages would change, so the first real run on main is
known in advance. --apply writes only the Slug column of those pages (Peter's call first).
Key: NOTION_TOKEN or NOTION_API_KEY.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ssot.bundle import all_bundles  # noqa: E402
from src.ssot.engine import plain  # noqa: E402
from src.ssot.markdown import rich_text  # noqa: E402


def main(argv=None, io=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if io is None:
        from src.ssot.notion_io import NotionIO
        io = NotionIO.from_env()
    rows = []
    for bundle in all_bundles(Path(args.repo) / "content" / "posts"):
        notion_id = bundle.meta.get("notion_id")
        if not notion_id:
            continue
        page = io.page(str(notion_id))
        current = plain((page.get("properties") or {}).get("Slug"))
        if current != bundle.slug:
            rows.append((page["id"], current, bundle.slug))
    print("| Notion page | Slug now | Slug planned (= folder) |\n|---|---|---|")
    for page_id, current, new in rows:
        print(f"| {page_id} | {current or '(empty)'} | {new} |")
        if args.apply:
            io.update_page(page_id, properties={"Slug": {"rich_text": rich_text(new)}})
    print(f"plan_notion_slugs: {len(rows)} pages {'changed' if args.apply else 'to change (dry-run)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
