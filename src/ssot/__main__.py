"""python -m src.ssot push|pull — see docs/REPO_SSOT.md.

    push --before SHA --after SHA        bundles changed by a push -> Notion (no --before = every bundle)
    push --slug SLUG [--slug …]          these bundles -> Notion
    pull [--page-id ID …] [--base main]  Notion edits -> commit on --base, or sync/notion-* branch + PR
Common: --database (or NOTION_DATABASE_ID_POSTS) --site https://example.com --only SLUG (allowlist)
        --dry-run (decide and print, write nothing) --add-sync-column (adds the SyncHash column once).
Key: NOTION_TOKEN or NOTION_API_KEY.
"""
import argparse
import json
import os
import sys

from .engine import Git, apply_pull, changed_slugs, check_schema, plan_pull, push
from .notion_io import NotionIO


def main(argv=None, io=None):
    parser = argparse.ArgumentParser(prog="python -m src.ssot", description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["push", "pull"])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--database", default=os.environ.get("NOTION_DATABASE_ID_POSTS", ""))
    parser.add_argument("--site", default=os.environ.get("SSOT_SITE", ""))
    parser.add_argument("--only", action="append", default=[o for o in os.environ.get("SSOT_ONLY", "").split(",") if o],
                        help="only these slugs (repeatable; env SSOT_ONLY=a,b)")
    parser.add_argument("--before")
    parser.add_argument("--after", default="HEAD")
    parser.add_argument("--slug", action="append", default=[])
    parser.add_argument("--page-id", action="append", default=[])
    parser.add_argument("--base", default="main")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--add-sync-column", action="store_true")
    parser.add_argument("--no-git-push", action="store_true", help="pull: commit locally, do not push (tests, local runs)")
    args = parser.parse_args(argv)
    if not args.database or not args.site.startswith("https://"):
        print("ssot: need --database (or NOTION_DATABASE_ID_POSTS) and an https --site", file=sys.stderr)
        return 2
    io = io or NotionIO.from_env()
    only = set(args.only)
    if args.command == "push":
        slugs = args.slug or changed_slugs(args.repo, args.before, args.after)
        results = push(io, args.database, args.repo, slugs, args.site, only=only, dry_run=args.dry_run,
                       add_column=args.add_sync_column)
    else:
        check_schema(io, args.database, args.add_sync_column, args.dry_run)
        results, changes = plan_pull(io, args.database, args.repo, args.site, page_ids=args.page_id, only=only)
        if not args.dry_run:
            results = [r for r in results if r.action not in ("commit", "pr", "none")]
            results += apply_pull(io, args.repo, changes, args.base, git=Git(args.repo), push=not args.no_git_push)
    for result in results:
        print(f"ssot {args.command}: {result.action} {result.slug} {result.detail}")
    summary = {}
    for result in results:
        summary[result.action] = summary.get(result.action, 0) + 1
    print("ssot summary " + json.dumps({"command": args.command, **summary}, sort_keys=True))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write(f"committed={summary.get('commit', 0)}\nprs={summary.get('pr', 0)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
