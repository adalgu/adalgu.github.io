"""push (repo -> Notion) and pull (Notion -> repo). Pure decisions + an IO object + a git object, so the
fake-client tests in tests/test_ssot_engine.py drive exactly the code the workflow runs."""
import hashlib
import json
import mimetypes
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

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


def bundle_url(site, slug, src, path=None):
    """![](cover.jpg) inside a bundle -> https://<site>/posts/<slug>/cover.jpg; absolute URLs stay.
    path = the page's public path when front matter `url:` sets it (BLOG-017 addendum 5: an ASCII folder keeping
    a Korean URL) — bundle files are published under the page URL, not the folder. Non-ASCII is percent-encoded."""
    if re.match(r"^[a-z]+://", src):
        return src
    base = path or f"/posts/{slug}/"
    base = "/" + base.strip("/") + "/"
    return f"{site.rstrip('/')}{quote(base)}{src.lstrip('./')}"


def page_path(bundle):
    """Public path of a bundle's page: front matter url if set, else /posts/<folder>/."""
    url = bundle.meta.get("url") if isinstance(bundle.meta, dict) else None
    return str(url) if url else f"/posts/{bundle.slug}/"


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
    url = bundle_url(site, bundle.slug, str(image), page_path(bundle))
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
    action: str  # same | write | create | skip | commit | pr | bot | unchanged | none
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


def git_paths(repo, *args):
    """Paths git prints, NUL-separated and unquoted. Plain output quotes non-ASCII names ("content/posts/\\354…"),
    which broke the first main push (BLOG-017 addendum 4: Korean bundle folder -> OSError Errno 36)."""
    out = subprocess.run(["git", "-c", "core.quotepath=off", "-C", str(repo), *args], check=True, capture_output=True)
    return [p for p in out.stdout.decode("utf-8").split("\0") if p]


def say(command, result):
    """One line per decision, printed the moment it is made — a run that dies half way still shows what it wrote."""
    print(f"ssot {command}: {result.action} {result.slug} {result.detail}", flush=True)
    return result


def edit_marker(page):
    """Trailer every Notion -> repo commit carries; once it is in the bundle's history the edit is in the repo."""
    return f"Notion-Edit: {page['id']} {page.get('last_edited_time', '')}"


def notion_edit_merged(repo, slug, page):
    """This exact Notion edit (page id + edit time) already reached the repo — e.g. its conflict PR was merged."""
    log = subprocess.run(["git", "-C", str(repo), "log", "--format=%B", "--", f"{POSTS}/{slug}"],
                         capture_output=True, text=True, check=False).stdout
    return edit_marker(page) in log


def push(io, database_id, repo, slugs, site, now=utcnow, only=(), dry_run=False, add_column=False,
         open_conflict=None):
    """open_conflict(slug) -> URL of an open sync/notion-<slug>-* PR or None (CLI: gh; tests: a fake)."""
    schema = check_schema(io, database_id, add_column, dry_run)
    results = []
    for slug in slugs:
        if only and slug not in only:
            results.append(say("push", Result(slug, "skip", "not in --only")))
            continue
        bundle = read_bundle(Path(repo) / POSTS / slug)
        if bundle is None:
            results.append(say("push", Result(slug, "skip", "no bundle (deleted bundles never delete Notion pages)")))
            continue
        page = find_page(io, database_id, bundle)
        hash_ = bundle.hash
        if page is not None:
            synced_hash, _ = sync_state(page)
            if synced_hash == hash_:
                results.append(say("push", Result(slug, "same", page["id"])))
                continue
            pr = open_conflict(slug) if open_conflict else None
            if pr:
                results.append(say("push", Result(slug, "skip", f"conflict PR open {pr} — Notion keeps its edit until it is merged")))
                continue
            if human_edit_since_sync(page) and not notion_edit_merged(repo, slug, page):
                # never overwrite a Notion edit that has not come back yet: pull turns it into a commit or a PR
                results.append(say("push", Result(slug, "skip", "Notion edit not in the repo yet — pull brings it back first")))
                continue
        blocks = md_to_blocks(bundle.body, image_url=lambda src: bundle_url(site, slug, src, page_path(bundle)))
        if dry_run:
            results.append(say("push", Result(slug, "write" if page else "create", "dry-run")))
            continue
        props, cover = page_properties(bundle, schema), page_cover(bundle, site)
        print(f"ssot push: writing {slug} {page['id'] if page else '(new page)'}", flush=True)
        if page is None:
            page = io.create_page(database_id, props, cover)
            io.append(page["id"], blocks)
            action = "create"
        else:
            io.update_page(page["id"], properties=props, cover=cover)
            io.replace_children(page["id"], blocks)
            action = "write"
        io.update_page(page["id"], properties={SYNC_PROP: sync_value(hash_, now())})  # last: body is in place
        results.append(say("push", Result(slug, action, page["id"])))
    return results


def changed_slugs(repo, before, after):
    """Bundles touched between two commits. No usable 'before' (new branch, first push) = every bundle."""
    if not before or set(before) == {"0"}:
        return [b.slug for b in all_bundles(Path(repo) / POSTS)]
    names = git_paths(repo, "diff", "-z", "--name-only", before, after, "--", POSTS)
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


def page_cover_back(cover, prefix, fetch, files):
    """Notion page cover -> (image, bundle-relative?) or None (no cover / http — mixed content, left as is).
    file (signed, expires in an hour) = downloaded into the bundle as cover-<content sha8>.<ext> (same picture,
    same name: re-pulling never renames). Our own bundle URL = that file again. Other https = kept as the URL:
    Hugo takes an absolute cover, pulling never fetches third-party pictures, and a person who pastes a link
    in Notion keeps a link."""
    cover = cover or {}
    kind = cover.get("type")
    url = (cover.get(kind) or {}).get("url", "") if kind else ""
    if not url:
        return None
    if kind == "file":
        content, content_type = fetch(url)
        ext = Path(urlparse(url).path).suffix.lower()
        if not ext or len(ext) > 5:
            ext = mimetypes.guess_extension((content_type or "").split(";")[0]) or ".png"
        name = f"cover-{hashlib.sha256(content).hexdigest()[:8]}{ext}"
        files[name] = content
        return name, True
    if url.startswith(prefix):
        return url[len(prefix):], True
    return (url, False) if url.startswith("https://") else None


def render_page(io, page, bundle, site, fetch):
    """-> (meta, body, new files). Notion file images are downloaded into the bundle (their URLs expire in an
    hour); external images that point at this bundle on the site go back to bundle-relative paths."""
    files = {}
    prefix = bundle_url(site, bundle.slug, "", page_path(bundle))

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
    cover = page_cover_back(page.get("cover"), prefix, fetch, files)
    old_cover = meta.get("cover") if isinstance(meta.get("cover"), dict) else {}
    if cover and cover[0] != old_cover.get("image"):
        image, relative = cover
        new_cover = {k: v for k, v in old_cover.items() if k != "relative"}
        new_cover["image"] = image
        if relative:
            new_cover["relative"] = True
        new_cover.setdefault("hiddenInSingle", False)  # the site hides covers by default (config cover.hidden*)
        new_cover.setdefault("hiddenInList", False)
        meta["cover"] = new_cover
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


def pr_branch(slug, page):
    return f"sync/notion-{slug}-{re.sub(r'[^0-9]', '', page.get('last_edited_time', ''))[:12]}"


def plan_pull(io, database_id, repo, site, page_ids=(), only=(), fetch=download, assume_person=False, git=None,
              pr_lookup=None):
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
        if notion_edit_merged(repo, slug, page):
            results.append(Result(slug, "skip", "this Notion edit is already in the repo (merged) — push writes Notion"))
            continue
        if git is not None and git.remote_has_branch(pr_branch(slug, page)):
            pr = (pr_lookup or (lambda b: gh_pr_for_branch(repo, b)))(pr_branch(slug, page))
            if pr:
                results.append(Result(slug, "skip", f"{pr_branch(slug, page)} has PR {pr} — waiting for its merge"))
            else:
                # BLOG-017 F5': branch pushed but its PR never opened (API failure) — a branch is not a finished job
                results.append(Result(slug, "pr", f"{pr_branch(slug, page)} without a PR — retrying the PR"))
                changes.append(Change(slug, page, "pr", "", {}, synced_hash, synced_hash, page.get("last_edited_time", "")))
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


def gh_pr_for_branch(repo, branch):  # pragma: no cover - needs gh + network
    """URL of any PR (open, closed or merged) whose head is this branch; None when there is none or gh fails
    (then the PR is created again: gh refuses a duplicate, so a wrong 'none' costs one refused call)."""
    out = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all", "--json", "url", "--limit", "1"],
                         cwd=repo, capture_output=True, text=True, check=False)
    try:
        found = json.loads(out.stdout) if out.returncode == 0 else []
    except ValueError:
        found = []
    return found[0]["url"] if found else None


def gh_pr(repo, branch, base, title, body):  # pragma: no cover - needs gh + network
    out = subprocess.run(["gh", "pr", "create", "--head", branch, "--base", base, "--title", title, "--body", body],
                         cwd=repo, check=True, capture_output=True, text=True)
    return out.stdout.strip()


def synced_commit(repo, slug, synced_hash, limit=50):
    """Newest commit whose copy of the bundle hashes to synced_hash — the version both sides last agreed on.
    The conflict branch starts there, so merging the PR is a real three-way merge of the two edits.
    None when not found (no git, history rewritten): the branch then starts at the base head."""
    folder = f"{POSTS}/{slug}"
    out = subprocess.run(["git", "-C", str(repo), "rev-list", f"-{limit}", "HEAD", "--", folder],
                         capture_output=True, text=True, check=False)
    if out.returncode != 0:
        return None
    for sha in out.stdout.split():
        try:
            names = git_paths(repo, "ls-tree", "-z", "--name-only", f"{sha}:{folder}")
        except subprocess.CalledProcessError:
            continue
        if "index.md" not in names:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / slug
            copy.mkdir()
            for name in names:
                blob = subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{folder}/{name}"],
                                      capture_output=True, check=False).stdout
                (copy / name).write_bytes(blob)
            bundle = read_bundle(copy)
            if bundle and bundle.hash == synced_hash:
                return sha
    return None


def gh_open_conflicts(repo):  # pragma: no cover - needs gh + network
    """-> open_conflict(slug) for push: URL of an open sync/notion-<slug>-* PR. gh missing or failing = no PR
    known; the person-edit guard still keeps Notion's edit (SyncHash is never moved by a PR)."""
    found = None

    def lookup(slug):
        nonlocal found
        if found is None:
            out = subprocess.run(["gh", "pr", "list", "--state", "open", "--json", "headRefName,url", "--limit", "200"],
                                 cwd=repo, capture_output=True, text=True, check=False)
            try:
                found = json.loads(out.stdout) if out.returncode == 0 else []
            except ValueError:
                found = []
            if out.returncode != 0:
                print("ssot: gh pr list failed — open conflict PRs unknown, the person-edit guard still applies")
        return next((pr["url"] for pr in found if pr["headRefName"].startswith(f"sync/notion-{slug}-")), None)
    return lookup


def _write(repo, change):
    folder = Path(repo) / POSTS / change.slug
    (folder / "index.md").write_text(change.index, encoding="utf-8")
    for name, data in change.files.items():
        (folder / name).write_bytes(data)
    return f"{POSTS}/{change.slug}"


def _open_conflict_pr(open_pr, repo, branch, base, change):
    return open_pr(repo, branch, base, f"sync(notion): {change.slug} — Notion and repo both changed",
                   f"Notion page {change.page['id']} was edited at {change.edited} while the repo copy also "
                   f"changed since the last sync ({change.synced_hash}).\n\nThis branch holds the Notion "
                   f"version of the bundle. Resolve against {base}; merging pushes the result back to Notion. "
                   f"Keep the commit trailer `{edit_marker(change.page)}` (merge, rebase or squash all keep it): "
                   f"that is how push knows this Notion edit is in the repo. Until then Notion is not overwritten.")


def apply_pull(io, repo, changes, base, now=utcnow, git=None, open_pr=gh_pr, push=True, pr_lookup=None):
    """Commits first, pushes, and only then stamps SyncHash — a failed push leaves Notion saying 'not synced',
    so the next run tries again instead of the repo later overwriting the Notion edit."""
    git = git or Git(repo)
    done = []
    commits = [c for c in changes if c.mode == "commit"]
    for change in commits:
        path = _write(repo, change)
        git.run("add", "--", path)
        git.run("commit", "-m", f"sync(notion): {change.slug} <- Notion edit {change.edited}\n\n"
                f"SyncHash {change.new_hash}\n{edit_marker(change.page)}")
    if commits and push:
        git.run("push", git.remote, f"HEAD:{base}")
    for change in commits:
        io.update_page(change.page["id"], properties={SYNC_PROP: sync_value(change.new_hash, now())})
        done.append(say("pull", Result(change.slug, "commit", git.head())))
    for change in [c for c in changes if c.mode == "pr"]:
        branch = pr_branch(change.slug, change.page)
        if push and git.remote_has_branch(branch):
            pr = (pr_lookup or (lambda b: gh_pr_for_branch(repo, b)))(branch)
            if pr:
                done.append(say("pull", Result(change.slug, "skip", f"{branch} has PR {pr}")))
            else:  # F5': the branch went up but the PR call failed last time — open the PR now, no new commit
                done.append(say("pull", Result(change.slug, "pr", _open_conflict_pr(open_pr, repo, branch, base, change))))
            continue
        start = synced_commit(repo, change.slug, change.synced_hash)
        git.run("checkout", "-q", "-b", branch, *([start] if start else []))
        try:
            path = _write(repo, change)
            git.run("add", "--", path)
            git.run("commit", "-m", f"sync(notion): {change.slug} <- Notion edit {change.edited} (repo also changed)\n\n"
                    f"{edit_marker(change.page)}")
            if push:
                git.run("push", "-u", git.remote, branch)
            url = _open_conflict_pr(open_pr, repo, branch, base, change)
        finally:
            git.run("checkout", "-q", base)
        # SyncHash is NOT touched here: the page keeps its person edit, so push leaves Notion alone until the PR is
        # merged (its Notion-Edit trailer then reaches the repo history) and pull skips the open branch
        done.append(say("pull", Result(change.slug, "pr", url)))
    for change in [c for c in changes if c.mode == "none"]:
        io.update_page(change.page["id"], properties={SYNC_PROP: sync_value(change.new_hash, now())})
    return done
