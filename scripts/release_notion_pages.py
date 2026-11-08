#!/usr/bin/env python3
"""BLOG-017 F5 rollback helper: hand the moved posts back to the old Notion -> Hugo import. Dry-run by default.

Only for going back to the old flow (Notion as the source) after reverting the repo-SSOT merge. The sync engine
marks every page it writes Source = hugo and skipRendering = on; the old importer skips such pages, so after a
revert those posts would vanish from the site. This sets, on pages of bundles that carry `notion_id` (the posts
moved from Notion), Source = notion and skipRendering = off. Nothing else: no body, no other column, no delete.

    python scripts/release_notion_pages.py            # list what would change
    python scripts/release_notion_pages.py --apply    # write
Key: NOTION_TOKEN or NOTION_API_KEY.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ssot.bundle import all_bundles  # noqa: E402
from src.ssot.engine import plain  # noqa: E402


def main(argv=None, io=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if io is None:
        from src.ssot.notion_io import NotionIO
        io = NotionIO.from_env()
    changed = 0
    for bundle in all_bundles(Path(args.repo) / "content" / "posts"):
        notion_id = bundle.meta.get("notion_id")
        if not notion_id:
            continue  # written in the repo first: there is no Notion original to hand back
        page = io.page(str(notion_id))
        props = page.get("properties") or {}
        want = {}
        if plain(props.get("Source")).lower() != "notion" and "Source" in props:
            want["Source"] = {"select": {"name": "notion"}}
        if (props.get("skipRendering") or {}).get("checkbox"):
            want["skipRendering"] = {"checkbox": False}
        if not want:
            continue
        changed += 1
        print(f"release: {'set' if args.apply else 'would set'} {sorted(want)} on {page['id']} ({bundle.slug})")
        if args.apply:
            io.update_page(page["id"], properties=want)
    print(f"release: {changed} pages {'changed' if args.apply else 'to change (dry-run)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
