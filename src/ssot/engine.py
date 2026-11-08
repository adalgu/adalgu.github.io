"""push (repo -> Notion) and pull (Notion -> repo). Pure decisions + an IO object + a git object, so the
fake-client tests in tests/test_ssot_engine.py drive exactly the code the workflow runs."""
import mimetypes
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .bundle import all_bundles, content_hash, file_hashes, read_bundle, render_index
from .markdown import md_to_blocks, blocks_to_markdown, rich_text, text_of_plain

SYNC_PROP = "SyncHash"   # rich_text: "<sha256:…> <ISO time>" — the bundle hash both sides last agreed on
POSTS = "content/posts"


# ---------- small helpers ----------

def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def plain(prop):
    if not prop:
        return ""
    kind = prop.get("type")
    if kind in ("rich_text", "title"):
        return text_of_plain(prop.get(kind))
    if kind == "select":
        return (prop.get("select") or {}).get("name", "")
    return ""


def sync_state(page):
    """-> (hash, time) from the SyncHash property; (None, None) when the page was never synced."""
    parts = plain((page.get("properties") or {}).get(SYNC_PROP)).split()
    if len(parts) >= 2 and parts[0].startswith("sha256:"):
        return parts[0], parse_time(parts[1])
    return None, None


def sync_value(hash_, moment):
    return {"rich_text": rich_text(f"{hash_} {iso(moment)}")}


def human_edit_since_sync(page):
    """Edited by a person after the last sync. Notion rounds last_edited_time down to the minute, so an edit in
    the same minute as the sync counts too — the content hash then decides whether anything changed."""
    if (page.get("last_edited_by") or {}).get("type") == "bot":
        return False  # every engine write ends with a bot as last editor: never pull our own writes
    _, synced = sync_state(page)
    edited = parse_time(page.get("last_edited_time"))
    if synced is None or edited is None:
        return False
    return edited >= synced.replace(second=0)


def bundle_url(site, slug, src):
    """![](cover.jpg) inside a bundle -> https://<site>/posts/<slug>/cover.jpg; absolute URLs stay."""
    if re.match(r"^[a-z]+://", src):
        return src
    return f"{site.rstrip('/')}/posts/{slug}/{src.lstrip('./')}"


def as_list(value):
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


# ---------- repo -> Notion ----------

def page_properties(bundle, schema, hash_=None, moment=None):
    """Only columns the DB has (Notion rejects unknown ones). Source = hugo marks a repo-owned page."""
    meta = bundle.meta
    props = {
        "Name": {"title": rich_text(str(meta.get("title") or bundle.slug))},
        "Slug": {"rich_text": rich_text(str(meta.get("slug") or bundle.slug))},
        "skipRendering": {"checkbox": True},  # the old Notion -> Hugo importer must not write this post again
        "isPublished": {"checkbox": not meta.get("draft", False)},
    }
    if meta.get("date"):
        props["Date"] = {"date": {"start": str(meta["date"]).replace(" ", "T")}}
    if meta.get("description"):
        props["Description"] = {"rich_text": rich_text(str(meta["description"]))}
    tags = [str(t).replace(",", " ") for t in as_list(meta.get("tags"))]
    props["Tags"] = {"multi_select": [{"name": t} for t in tags]}
    categories = as_list(meta.get("categories"))
    if categories:
        props["Category"] = {"select": {"name": str(categories[0]).replace(",", " ")}}
    if schema.get("Source") == "select":
        props["Source"] = {"select": {"name": "hugo"}}
    elif schema.get("Source") == "rich_text":
        props["Source"] = {"rich_text": rich_text("hugo")}
    if hash_:
        props[SYNC_PROP] = sync_value(hash_, moment)
    return {name: value for name, value in props.items() if name in schema}


def page_cover(bundle, site):
    image = ((bundle.meta.get("cover") or {}) if isinstance(bundle.meta.get("cover"), dict) else {}).get("image")
    if not image:
        return None
    url = bundle_url(site, bundle.slug, str(image))
    return {"type": "external", "external": {"url": url}} if url.startswith("https://") else None


def find_page(io, database_id, bundle):
    """notion_id in front matter first (moved Notion posts), then Slug among repo-owned pages."""
    notion_id = bundle.meta.get("notion_id")
    if notion_id:
        try:
            page = io.page(str(notion_id))
            if not page.get("archived") and not page.get("in_trash"):
                return page
        except Exception:  # deleted or no access: fall back to the slug
            pass
    slug = str(bundle.meta.get("slug") or bundle.slug)
    pages = [p for p in io.query(database_id, {"property": "Slug", "rich_text": {"equals": slug}})
             if not p.get("archived") and not p.get("in_trash") and plain(p["properties"].get("Source")).lower() in ("hugo", "")]
    if len(pages) > 1:
        raise RuntimeError(f"ssot: {len(pages)} Notion pages with Slug {slug} — fix by hand, nothing written")
    return pages[0] if pages else None


@dataclass
class Result:
    slug: str
    action: str  # same | write | create | skip | commit | pr | bot | unchanged | conflict-pending | none
    detail: str = ""


def check_schema(io, database_id, add_column=False, dry_run=False):
    schema = {name: prop.get("type") for name, prop in io.database(database_id).get("properties", {}).items()}
    if SYNC_PROP not in schema:
        if dry_run:
            print(f"ssot: DB has no {SYNC_PROP} column yet (a real run needs --add-sync-column)")
            schema[SYNC_PROP] = "rich_text"
            return schema
        if not add_column:
            raise SystemExit(f"ssot: DB has no {SYNC_PROP} column (rich_text) — rerun with --add-sync-column (adds one column, removes nothing)")
        io.add_property(database_id, SYNC_PROP, {"rich_text": {}})
        schema[SYNC_PROP] = "rich_text"
    return schema


def push(io, database_id, repo, slugs, site, now=utcnow, only=(), dry_run=False, add_column=False):
    schema = check_schema(io, database_id, add_column, dry_run)
    results = []
    for slug in slugs:
        if only and slug not in only:
            results.append(Result(slug, "skip", "not in --only"))
            continue
        bundle = read_bundle(Path(repo) / POSTS / slug)
        if bundle is None:
            results.append(Result(slug, "skip", "no bundle (deleted bundles never delete Notion pages)"))
            continue
        page = find_page(io, database_id, bundle)
        hash_ = bundle.hash
        if page is not None:
            synced_hash, _ = sync_state(page)
            if synced_hash == hash_:
                results.append(Result(slug, "same", page["id"]))
                continue
            if human_edit_since_sync(page):
                # never overwrite a Notion edit that has not come back yet: pull turns it into a PR
                results.append(Result(slug, "conflict-pending", page["id"]))
                continue
        blocks = md_to_blocks(bundle.body, image_url=lambda src: bundle_url(site, slug, src))
        if dry_run:
            results.append(Result(slug, "write" if page else "create", "dry-run"))
            continue
        props, cover = page_properties(bundle, schema), page_cover(bundle, site)
        if page is None:
            page = io.create_page(database_id, props, cover)
            io.append(page["id"], blocks)
            action = "create"
        else:
            io.update_page(page["id"], properties=props, cover=cover)
            io.replace_children(page["id"], blocks)
            action = "write"
        io.update_page(page["id"], properties={SYNC_PROP: sync_value(hash_, now())})  # last: body is in place
        results.append(Result(slug, action, page["id"]))
    return results


def changed_slugs(repo, before, after):
    """Bundles touched between two commits. No usable 'before' (new branch, first push) = every bundle."""
    if not before or set(before) == {"0"}:
        return [b.slug for b in all_bundles(Path(repo) / POSTS)]
    names = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", before, after, "--", POSTS],
                           check=True, capture_output=True, text=True).stdout.split()
    return sorted({Path(n).parts[2] for n in names if len(Path(n).parts) > 3})


# ---------- Notion -> repo ----------

@dataclass
class Change:
    slug: str
    page: dict
    mode: str          # commit | pr
    index: str         # new index.md text
    files: dict        # new file name -> bytes (downloaded Notion images)
    new_hash: str
    synced_hash: str
    edited: str        # page last_edited_time


def download(url):  # pragma: no cover - network; tests pass their own fetch
    import requests
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content, response.headers.get("content-type", "")


def _image_name(block, url, content_type):
    ext = Path(urlparse(url).path).suffix.lower()
    if not ext or len(ext) > 5:
        ext = mimetypes.guess_extension((content_type or "").split(";")[0]) or ".png"
    return f"notion-{block['id'].replace('-', '')[:12]}{ext}"


def render_page(io, page, bundle, site, fetch):
    """-> (meta, body, new files). Notion file images are downloaded into the bundle (their URLs expire in an
    hour); external images that point at this bundle on the site go back to bundle-relative paths."""
    files = {}
    prefix = bundle_url(site, bundle.slug, "")

    def image_src(block):
        data = block["image"]
        kind = data.get("type")
        url = (data.get(kind) or {}).get("url", "")
        if kind == "file":
            content, content_type = fetch(url)
            name = _image_name(block, url, content_type)
            files[name] = content
            return name
        return url[len(prefix):] if url.startswith(prefix) else url

    body = blocks_to_markdown(io.children(page["id"]), io.children, image_src)
    props = page.get("properties") or {}
    meta = dict(bundle.meta)
    title = plain(props.get("Name"))
    if title:
        meta["title"] = title
    if "Description" in props:
        description = plain(props.get("Description"))
        if description or "description" in meta:
            meta["description"] = description
    if "Tags" in props and (props["Tags"].get("multi_select") or "tags" in meta):
        meta["tags"] = [t["name"] for t in props["Tags"].get("multi_select") or []]
    return meta, body, files


def plan_pull(io, database_id, repo, site, page_ids=(), only=(), fetch=download, assume_person=False):
    """Decide what comes back. Nothing is written here.
    assume_person (test hook, needs explicit page_ids): treat these pages' last edit as a person's even when an
    integration made it — agents edit Notion through the same integration the engine uses."""
    if assume_person and not page_ids:
        raise SystemExit("ssot: --assume-person-edit needs --page-id (one test page, never a whole DB scan)")
    bundles = all_bundles(Path(repo) / POSTS)
    by_id = {str(b.meta.get("notion_id")).replace("-", ""): b for b in bundles if b.meta.get("notion_id")}
    by_slug = {str(b.meta.get("slug") or b.slug): b for b in bundles}
    pages = [io.page(pid) for pid in page_ids] if page_ids else io.query(database_id)
    results, changes = [], []
    for page in pages:
        bundle = by_id.get(page["id"].replace("-", "")) or by_slug.get(plain(page["properties"].get("Slug")))
        if bundle is None:
            continue  # not a repo post (yet)
        slug = bundle.slug
        if only and slug not in only:
            continue
        if page.get("archived") or page.get("in_trash"):
            results.append(Result(slug, "skip", "archived in Notion (pull never deletes)"))
            continue
        synced_hash, _ = sync_state(page)
        if synced_hash is None:
            results.append(Result(slug, "skip", "never synced (push first)"))
            continue
        if assume_person:
            page = dict(page, last_edited_by={**(page.get("last_edited_by") or {}), "type": "person"})
        if not human_edit_since_sync(page):
            bot = (page.get("last_edited_by") or {}).get("type") == "bot"
            results.append(Result(slug, "bot" if bot else "unchanged", page["id"]))
            continue
        meta, body, files = render_page(io, page, bundle, site, fetch)
        new_hash = content_hash(meta, body, file_hashes(bundle.path, files))
        if new_hash in (synced_hash, bundle.hash):
            # touched but nothing to bring back; when Notion now equals the repo, that is the agreed hash
            agreed = bundle.hash if new_hash == bundle.hash else synced_hash
            results.append(Result(slug, "none", "Notion touched, content same"))
            changes.append(Change(slug, page, "none", "", {}, agreed, synced_hash, page.get("last_edited_time", "")))
            continue
        mode = "commit" if bundle.hash == synced_hash else "pr"
        changes.append(Change(slug, page, mode, render_index(bundle, meta, body), files, new_hash, synced_hash,
                              page.get("last_edited_time", "")))
        results.append(Result(slug, mode, page["id"]))
    return results, changes


class Git:
    def __init__(self, repo, remote="origin"):
        self.repo, self.remote = str(repo), remote

    def run(self, *args, check=True):
        return subprocess.run(["git", "-C", self.repo, *args], check=check, capture_output=True, text=True)

    def remote_has_branch(self, branch):
        return bool(self.run("ls-remote", "--heads", self.remote, branch).stdout.strip())

    def head(self):
        return self.run("rev-parse", "HEAD").stdout.strip()


def gh_pr(repo, branch, base, title, body):  # pragma: no cover - needs gh + network
    out = subprocess.run(["gh", "pr", "create", "--head", branch, "--base", base, "--title", title, "--body", body],
                         cwd=repo, check=True, capture_output=True, text=True)
    return out.stdout.strip()


def _write(repo, change):
    folder = Path(repo) / POSTS / change.slug
    (folder / "index.md").write_text(change.index, encoding="utf-8")
    for name, data in change.files.items():
        (folder / name).write_bytes(data)
    return f"{POSTS}/{change.slug}"


def apply_pull(io, repo, changes, base, now=utcnow, git=None, open_pr=gh_pr, push=True):
    """Commits first, pushes, and only then stamps SyncHash — a failed push leaves Notion saying 'not synced',
    so the next run tries again instead of the repo later overwriting the Notion edit."""
    git = git or Git(repo)
    done = []
    commits = [c for c in changes if c.mode == "commit"]
    for change in commits:
        path = _write(repo, change)
        git.run("add", "--", path)
        git.run("commit", "-m", f"sync(notion): {change.slug} <- Notion edit {change.edited}\n\nSyncHash {change.new_hash}")
    if commits and push:
        git.run("push", git.remote, f"HEAD:{base}")
    for change in commits:
        io.update_page(change.page["id"], properties={SYNC_PROP: sync_value(change.new_hash, now())})
        done.append(Result(change.slug, "commit", git.head()))
    for change in [c for c in changes if c.mode == "pr"]:
        stamp = re.sub(r"[^0-9]", "", change.edited)[:12] or iso(now())
        branch = f"sync/notion-{change.slug}-{stamp}"
        if push and git.remote_has_branch(branch):
            done.append(Result(change.slug, "skip", f"{branch} already open"))
            continue
        git.run("checkout", "-q", "-b", branch)
        try:
            path = _write(repo, change)
            git.run("add", "--", path)
            git.run("commit", "-m", f"sync(notion): {change.slug} <- Notion edit {change.edited} (repo also changed)")
            if push:
                git.run("push", "-u", git.remote, branch)
            url = open_pr(repo, branch, base, f"sync(notion): {change.slug} — Notion and repo both changed",
                          f"Notion page {change.page['id']} was edited at {change.edited} while the repo copy also "
                          f"changed since the last sync ({change.synced_hash}).\n\nThis branch holds the Notion "
                          f"version of the bundle. Resolve against {base}; merging pushes the result back to Notion.")
        finally:
            git.run("checkout", "-q", base)
        # the Notion edit now lives in the PR: mark it consumed (same hash, new time) so it is not pulled twice
        io.update_page(change.page["id"], properties={SYNC_PROP: sync_value(change.synced_hash, now())})
        done.append(Result(change.slug, "pr", url))
    for change in [c for c in changes if c.mode == "none"]:
        io.update_page(change.page["id"], properties={SYNC_PROP: sync_value(change.new_hash, now())})
    return done
