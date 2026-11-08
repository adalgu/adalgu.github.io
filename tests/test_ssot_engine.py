"""Repo-SSOT sync engine against a fake Notion (client.request level, 100 per page, minute-rounded
last_edited_time, bot/person editors) and real git repos in a temp folder. Network 0."""
import contextlib
import copy
import io
import os
import subprocess
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from src.ssot import engine
from src.ssot.__main__ import main as cli
from src.ssot.markdown import blocks_to_markdown, md_to_blocks
from src.ssot.notion_io import NotionIO

SITE = "https://blog.example"
DB = "db-1"
SCHEMA = {"Name": "title", "Slug": "rich_text", "Date": "date", "Tags": "multi_select", "Category": "select",
          "Description": "rich_text", "Source": "select", "isPublished": "checkbox", "skipRendering": "checkbox"}
POST = """---
title: "시험 글"
date: 2026-11-01T14:00:00+09:00
slug: hello
description: "설명"
tags: ["시험", "hugo"]
draft: false
cover:
  image: cover.jpg
  relative: true
---

첫 문단 **굵게** 와 *기울임* 그리고 [링크](https://gunn.kim/) `코드`.
둘째 줄은 같은 문단.

## 소제목

- 하나
- 둘

1. 첫째
2. 둘째

> 인용 한 줄
> 인용 두 줄

```python
print("hi")
```

![표지 설명](cover.jpg)

---

끝 문단.
"""


def read_form(items):
    out = []
    for item in items or []:
        text = item.get("text") or {}
        marks = {k: False for k in ("bold", "italic", "strikethrough", "underline", "code")}
        marks.update(item.get("annotations") or {})
        out.append({"type": "text", "plain_text": text.get("content", ""), "href": (text.get("link") or {}).get("url"),
                    "annotations": marks, "text": text})
    return out


class FakeClient:
    """notion_client.Client.request look-alike."""

    def __init__(self, schema=SCHEMA):
        self.schema = dict(schema)
        self.pages, self.children = {}, {}
        self.clock = datetime(2026, 11, 9, 1, 0, tzinfo=timezone.utc)
        self.seq = 0
        self.calls = []
        self.users_forbidden = False  # True = integration without the user-information capability

    # helpers
    def now(self):
        return self.clock

    def _id(self, prefix):
        self.seq += 1
        return f"{prefix}{self.seq:04d}-aaaa-bbbb-cccc-dddddddddddd"

    def touch(self, page_id, editor="bot"):
        self.clock += timedelta(minutes=1)
        page = self.pages[page_id]
        page["last_edited_time"] = self.clock.strftime("%Y-%m-%dT%H:%M:00.000Z")
        page["last_edited_by"] = {"object": "user", "id": "u-" + editor}  # real pages carry no type here

    def _owner(self, block_id):
        if block_id in self.pages:
            return block_id
        for parent, blocks in self.children.items():
            if any(b["id"] == block_id for b in blocks):
                return self._owner(parent)
        return None

    def _store_props(self, page, props):
        for name, value in props.items():
            kind = self.schema.get(name) or next(iter(value))
            if kind in ("title", "rich_text"):
                page["properties"][name] = {"type": kind, kind: read_form(value[kind])}
            else:
                page["properties"][name] = {"type": kind, kind: value[kind]}

    def _store_blocks(self, parent, blocks):
        for block in blocks:
            kind = block["type"]
            data = dict(block.get(kind) or {})
            for key in ("rich_text", "caption"):
                if key in data:
                    data[key] = read_form(data[key])
            if "cells" in data:  # table_row: each cell is a rich text array
                data["cells"] = [read_form(cell) for cell in data["cells"]]
            nested = data.pop("children", None)  # Notion stores nested children (a table's rows) under the block
            stored = {"object": "block", "id": self._id("b"), "type": kind, kind: data, "has_children": bool(nested)}
            self.children.setdefault(parent, []).append(stored)
            if nested:
                self._store_blocks(stored["id"], nested)

    def human_edit(self, page_id, change, editor="person"):
        change(self.children[page_id])
        self.touch(page_id, editor)

    def _page(self, items, body):
        at = 0
        if body.get("start_cursor"):
            at = next(i for i, x in enumerate(items) if x["id"] == body["start_cursor"])
        size = min(int(body.get("page_size") or 100), 100)
        more = at + size < len(items)
        return {"results": items[at:at + size], "has_more": more, "next_cursor": items[at + size]["id"] if more else None}

    # the one entry point
    def request(self, path, method, query=None, body=None):
        self.calls.append((method, path))
        parts = path.split("/")
        body = body or {}
        if parts[0] == "users":
            if parts[1] == "me":
                return {"object": "user", "id": "u-bot", "type": "bot"}
            if self.users_forbidden:
                raise RuntimeError("403 restricted_resource")
            return {"object": "user", "id": parts[1], "type": parts[1][2:]}
        if parts[0] == "databases":
            if len(parts) == 3 and parts[2] == "query":
                pages = list(self.pages.values())
                flt = body.get("filter")
                if flt:
                    want = flt["rich_text"]["equals"]
                    pages = [p for p in pages if engine.plain(p["properties"].get(flt["property"])) == want]
                return self._page(copy.deepcopy(pages), body)
            if method == "PATCH":
                for name, spec in body["properties"].items():
                    self.schema[name] = next(iter(spec))
            return {"properties": {k: {"type": v} for k, v in self.schema.items()}}
        if parts[0] == "pages":
            if method == "POST":
                page_id = self._id("p")
                self.pages[page_id] = {"object": "page", "id": page_id, "archived": False, "properties": {},
                                       "cover": body.get("cover")}
                self._store_props(self.pages[page_id], body["properties"])
                self.touch(page_id)
                return self.pages[page_id]
            page = self.pages[parts[1]]
            if method == "GET":
                return copy.deepcopy(page)
            if method == "PATCH":
                self._store_props(page, body.get("properties") or {})
                if body.get("cover"):
                    page["cover"] = body["cover"]
                self.touch(page["id"])
            return page
        if parts[0] == "blocks":
            if method == "DELETE":
                owner = self._owner(parts[1])
                for blocks in self.children.values():
                    blocks[:] = [b for b in blocks if b["id"] != parts[1]]
                self.touch(owner)
                return {}
            if method == "PATCH":
                self._store_blocks(parts[1], body["children"])
                self.touch(self._owner(parts[1]))
                return {}
            return self._page(self.children.get(parts[1], []), query or {})
        raise AssertionError(path)

    def writes(self, page_id=None):
        return [c for c in self.calls if c[0] in ("PATCH", "DELETE", "POST") and not c[1].startswith("databases")
                and not c[1].endswith("/query")]


def rich(text):
    return [{"type": "text", "text": {"content": text}}]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


class Repo:
    def __init__(self, root):
        self.remote = Path(root) / "remote.git"
        self.path = Path(root) / "work"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.path)], check=True)
        git(self.path, "config", "user.email", "t@example.com")
        git(self.path, "config", "user.name", "t")
        git(self.path, "remote", "add", "origin", str(self.remote))
        self.write("hello", POST, {"cover.jpg": b"jpeg-bytes"})
        self.commit("add hello")
        git(self.path, "push", "-q", "origin", "main")

    def write(self, slug, text, files=None):
        folder = self.path / "content" / "posts" / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.md").write_text(text, encoding="utf-8")
        for name, data in (files or {}).items():
            (folder / name).write_bytes(data)

    def commit(self, message):
        git(self.path, "add", "-A")
        git(self.path, "commit", "-q", "-m", message)
        return git(self.path, "rev-parse", "HEAD")

    def index(self, slug="hello"):
        return (self.path / "content" / "posts" / slug / "index.md").read_text(encoding="utf-8")

    def remote_log(self, ref="main"):
        return git(self.remote, "log", "--format=%s", ref).splitlines()


def edit_paragraph(old, new):
    def change(blocks):
        for block in blocks:
            data = block.get(block["type"]) or {}
            for item in data.get("rich_text", []):
                if old in item["plain_text"]:
                    item["plain_text"] = item["plain_text"].replace(old, new)
                    item["text"]["content"] = item["plain_text"]
    return change


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repo(self.tmp.name)
        self.client = FakeClient()
        self.io = NotionIO(self.client)
        self.prs = []

    def push(self, slugs=("hello",), **kw):
        return engine.push(self.io, DB, self.repo.path, list(slugs), SITE, now=self.client.now, add_column=True, **kw)

    def pr_lookup(self, branch):  # the fake GitHub: PRs opened through open_pr, by head branch
        return next((f"pr/{n}" for n, a in enumerate(self.prs, 1) if a[1] == branch), None)

    def pull(self, fetch=None, open_pr=None):
        results, changes = engine.plan_pull(self.io, DB, self.repo.path, SITE, fetch=fetch or self.fail_fetch,
                                            git=engine.Git(self.repo.path), pr_lookup=self.pr_lookup)
        done = engine.apply_pull(self.io, self.repo.path, changes, "main", now=self.client.now,
                                 open_pr=open_pr or (lambda *a: self.prs.append(a) or f"pr/{len(self.prs)}"),
                                 pr_lookup=self.pr_lookup)
        return [r for r in results if r.action not in ("commit", "pr", "none")] + done

    @staticmethod
    def fail_fetch(url):
        raise AssertionError(f"unexpected download {url}")

    def page(self):
        (page,) = self.client.pages.values()
        return page

    def test_markdown_round_trip_is_stable(self):
        body = POST.split("---", 2)[2].lstrip("\n")
        client = FakeClient()
        client.pages["p"] = {"id": "p"}
        client._store_blocks("p", md_to_blocks(body, image_url=lambda s: engine.bundle_url(SITE, "hello", s)))
        prefix = engine.bundle_url(SITE, "hello", "")

        def image_src(block):
            url = block["image"]["external"]["url"]
            return url[len(prefix):] if url.startswith(prefix) else url
        self.assertEqual(blocks_to_markdown(client.children["p"], image_src=image_src), body)

    def test_repo_change_writes_notion_once_and_nothing_comes_back(self):
        self.assertEqual([r.action for r in self.push()], ["create"])
        page = self.page()
        self.assertEqual(engine.plain(page["properties"]["Source"]), "hugo")
        self.assertEqual(page["cover"]["external"]["url"], f"{SITE}/posts/hello/cover.jpg")
        self.assertTrue(engine.sync_state(page)[0].startswith("sha256:"))
        images = [b for b in self.client.children[page["id"]] if b["type"] == "image"]
        self.assertEqual(images[0]["image"]["external"]["url"], f"{SITE}/posts/hello/cover.jpg")
        before = len(self.client.writes())
        self.assertEqual([r.action for r in self.push()], ["same"])  # same post twice = 0 writes
        self.assertEqual([r.action for r in self.pull()], ["bot"])  # our own write never comes back
        self.assertEqual(len(self.client.writes()), before)
        self.assertEqual(self.repo.remote_log(), ["add hello"])
        self.assertEqual(len(self.client.pages), 1)

    def test_notion_edit_commits_once_then_push_writes_nothing(self):
        self.push()
        page_id = self.page()["id"]
        self.client.human_edit(page_id, edit_paragraph("끝 문단.", "끝 문단을 노션에서 고침."))
        before_sha = git(self.repo.path, "rev-parse", "HEAD")
        self.assertEqual([r.action for r in self.pull()], ["commit"])
        self.assertIn("끝 문단을 노션에서 고침.", self.repo.index())
        self.assertIn('title: "시험 글"', self.repo.index())  # front matter kept byte for byte
        self.assertTrue(self.repo.remote_log()[0].startswith("sync(notion): hello <- Notion edit 2026-11-09T"))
        self.assertEqual(len(self.repo.remote_log()), 2)
        writes = len(self.client.writes())
        after_sha = git(self.repo.path, "rev-parse", "HEAD")
        slugs = engine.changed_slugs(self.repo.path, before_sha, after_sha)
        self.assertEqual(slugs, ["hello"])
        self.assertEqual([r.action for r in self.push(slugs)], ["same"])  # hash equal: Notion not rewritten
        self.assertEqual([r.action for r in self.pull()], ["bot"])  # and nothing comes back again
        self.assertEqual(len(self.client.writes()), writes)
        self.assertEqual(len(self.repo.remote_log()), 2)

    def test_both_sides_changed_open_one_pr_and_leave_main(self):
        self.push()
        page_id = self.page()["id"]
        self.repo.write("hello", POST.replace("끝 문단.", "끝 문단을 저장소에서 고침."))
        self.repo.commit("repo edit")
        git(self.repo.path, "push", "-q", "origin", "main")
        self.client.human_edit(page_id, edit_paragraph("첫 문단", "노션에서 고친 첫 문단"))
        self.assertEqual([r.action for r in self.push()], ["skip"])  # Notion edit not overwritten
        main_before = git(self.repo.remote, "rev-parse", "main")
        results = self.pull()
        self.assertEqual([r.action for r in results], ["pr"])
        self.assertEqual(len(self.prs), 1)
        branch = self.prs[0][1]
        self.assertTrue(branch.startswith("sync/notion-hello-2026"))
        self.assertEqual(git(self.repo.remote, "rev-parse", "main"), main_before)  # main untouched
        self.assertIn("노션에서 고친 첫 문단", git(self.repo.remote, "show", f"{branch}:content/posts/hello/index.md"))
        self.assertEqual(git(self.repo.path, "rev-parse", "--abbrev-ref", "HEAD"), "main")

        # BLOG-017 F3: PR not merged yet -> pushing the repo copy again leaves the Notion edit alone
        notion_body = lambda: blocks_to_markdown(self.client.children[page_id])
        self.assertEqual([r.action for r in self.push()], ["skip"])
        skipped = self.push(open_conflict=lambda slug: "https://github.example/pr/1")
        self.assertIn("conflict PR open https://github.example/pr/1", skipped[0].detail)
        self.assertIn("노션에서 고친 첫 문단", notion_body())
        self.assertNotIn("저장소에서 고침", notion_body())
        self.assertEqual([r.action for r in self.pull()], ["skip"])  # branch open: no second PR, no re-render
        self.assertEqual(len(self.prs), 1)

        # the branch starts at the version both sides agreed on, so merging it is a real three-way merge
        git(self.repo.path, "fetch", "-q", "origin")
        git(self.repo.path, "merge", "-q", "--no-edit", f"origin/{branch}")
        merged = self.repo.index()
        self.assertIn("노션에서 고친 첫 문단", merged)
        self.assertIn("끝 문단을 저장소에서 고침.", merged)
        git(self.repo.path, "push", "-q", "origin", "main")
        self.assertEqual([r.action for r in self.pull()], ["skip"])  # merged edit: pull leaves it to push
        self.assertEqual([r.action for r in self.push()], ["write"])  # merged: the repo is the truth again
        self.assertIn("노션에서 고친 첫 문단", notion_body())
        self.assertIn("저장소에서 고침", notion_body())
        self.assertEqual([r.action for r in self.pull()], ["bot"])
        self.assertEqual([r.action for r in self.push()], ["same"])

    def test_failed_pr_call_is_retried_on_the_next_run(self):
        # BLOG-017 F5' (Anton engine-edge-probe failed_pr_retry): branch pushed, PR API failed
        self.push()
        page_id = self.page()["id"]
        self.repo.write("hello", POST.replace("끝 문단.", "저장소 쪽 고침."))
        self.repo.commit("repo edit")
        git(self.repo.path, "push", "-q", "origin", "main")
        self.client.human_edit(page_id, edit_paragraph("첫 문단", "노션 쪽 고침"))

        def broken(*args):
            raise RuntimeError("PR API down")
        with self.assertRaises(RuntimeError):
            self.pull(open_pr=broken)
        branches = git(self.repo.remote, "for-each-ref", "--format=%(refname)", "refs/heads/sync").splitlines()
        self.assertEqual(len(branches), 1)
        self.assertEqual(self.prs, [])
        self.assertEqual([r.action for r in self.pull()], ["pr"])  # branch without PR = retry, not skip
        self.assertEqual(len(self.prs), 1)
        self.assertEqual(self.prs[0][1], branches[0].removeprefix("refs/heads/"))
        self.assertEqual(len(git(self.repo.remote, "for-each-ref", "--format=%(refname)", "refs/heads/sync").splitlines()), 1)
        self.assertEqual([r.action for r in self.pull()], ["skip"])  # PR now exists: nothing more
        self.assertEqual(len(self.prs), 1)

    TABLE_MD = ("앞 문단.\n\n| 이론 | 핵심 | 실전 | 연구 |\n| --- | --- | --- | --- |\n"
                + "".join(f"| 행{n} | **굵게{n}** | `코드{n}` | 끝{n} |\n" for n in range(1, 8)) + "\n뒤 문단.\n")

    def test_table_round_trip(self):
        # BLOG-017 addendum 6 (Anton round 5 P1): an 8-row x 4-column table must reach Notion as a table, not a paragraph
        blocks = md_to_blocks(self.TABLE_MD)
        self.assertEqual([b["type"] for b in blocks], ["paragraph", "table", "paragraph"])
        table = blocks[1]["table"]
        self.assertEqual((table["table_width"], table["has_column_header"], len(table["children"])), (4, True, 8))
        self.repo.write("tabled", POST.replace("slug: hello", "slug: tabled").split("---\n\n", 1)[0] + "---\n\n" + self.TABLE_MD)
        self.repo.commit("table post")
        self.push(["tabled"])
        page_id = next(p["id"] for p in self.client.pages.values() if engine.plain(p["properties"]["Slug"]) == "tabled")
        stored = self.client.children[page_id]
        self.assertEqual([b["type"] for b in stored], ["paragraph", "table", "paragraph"])  # block kinds same
        rows = self.client.children[stored[1]["id"]]
        self.assertEqual([b["type"] for b in rows], ["table_row"] * 8)
        self.assertEqual(sum(len(r["table_row"]["cells"]) for r in rows), 32)  # cell count same
        # and back: Notion -> Markdown gives the same table text, so a pull of an untouched page changes nothing
        self.assertEqual(blocks_to_markdown(stored, self.client.children.get), self.TABLE_MD)
        self.assertEqual([r.action for r in self.pull()], ["bot"])

    def test_table_header_settings_round_trip_all_four(self):
        # BLOG-017 addendum 7 (Anton round 6): has_column_header / has_row_header used to come back as (True, False)
        from src.ssot.markdown import table_block
        rows = ["| 항목 | 값 |", "| --- | --- |", "| 가 | 1 |", "| 나 | 2 |"]
        for flags in ((True, False), (False, False), (True, True), (False, True)):
            with self.subTest(flags=flags):
                client = FakeClient()
                client.pages["p"] = {"id": "p"}
                client._store_blocks("p", [{"type": "paragraph", "paragraph": {"rich_text": rich("앞")}}, table_block(rows, flags)])
                md = blocks_to_markdown(client.children["p"], client.children.get)
                self.assertEqual("notion-table:" in md, flags != (True, False))  # default needs no note
                back = [b for b in md_to_blocks(md) if b["type"] == "table"][0]["table"]
                self.assertEqual((back["has_column_header"], back["has_row_header"]), flags)
                self.assertEqual(len(back["children"]), 3)
                self.assertEqual([b["type"] for b in md_to_blocks(md)], ["paragraph", "table"])  # the note is no paragraph
                client2 = FakeClient()
                client2.pages["p"] = {"id": "p"}
                client2._store_blocks("p", md_to_blocks(md))
                self.assertEqual(blocks_to_markdown(client2.children["p"], client2.children.get), md)  # stable

    def test_a_stray_note_without_a_table_stays_text(self):
        md = "<!-- notion-table: column_header=false row_header=true -->\n\n문단.\n"
        self.assertEqual([b["type"] for b in md_to_blocks(md)], ["paragraph", "paragraph"])

    def test_table_cells_with_escaped_pipe_and_short_rows(self):
        blocks = md_to_blocks("| a | b \\| c |\n|---|---|\n| 1 |\n")
        rows = blocks[0]["table"]["children"]
        self.assertEqual(blocks[0]["table"]["table_width"], 2)
        self.assertEqual([[c[0]["text"]["content"] if c else "" for c in r["table_row"]["cells"]] for r in rows],
                         [["a", "b | c"], ["1", ""]])

    def test_korean_bundle_folder_in_push_range(self):
        # BLOG-017 addendum 4: run 42507506203 died with Errno 36 on a Korean bundle folder (git quoted the path)
        slug = "스몰토크는-왜-중요한가"
        before = git(self.repo.path, "rev-parse", "HEAD")
        self.repo.write(slug, POST.replace("slug: hello", f"slug: {slug}"), {"cover.jpg": b"jpeg"})
        self.repo.write("hello", POST.replace("끝 문단.", "끝 문단 바꿈."))
        after = self.repo.commit("korean bundle")
        slugs = engine.changed_slugs(self.repo.path, before, after)
        self.assertEqual(slugs, sorted(["hello", slug]))
        results = self.push(slugs)
        self.assertEqual(sorted(r.action for r in results), ["create", "create"])
        page = next(p for p in self.client.pages.values() if engine.plain(p["properties"]["Slug"]) == slug)
        self.assertEqual(page["cover"]["external"]["url"], f"{SITE}/posts/{quote(slug)}/cover.jpg")  # percent-encoded
        # the conflict-branch start point reads the same folder through git ls-tree
        self.assertEqual(engine.synced_commit(self.repo.path, slug, engine.read_bundle(self.repo.path / "content/posts" / slug).hash),
                         after)

    def test_ascii_folder_rule(self):
        from src.ssot.bundle import ascii_folder
        self.assertEqual(ascii_folder("github-actions-60day-inactivity-trap", "2025-09-06"), "github-actions-60day-inactivity-trap")
        self.assertEqual(ascii_folder("스몰토크는-왜-중요한가", "2026-05-15", "3617522e-eb2f-805c-992e-e2619356e918"),
                         "post-20260515-3617522e")
        self.assertEqual(ascii_folder("Mixed 한글", "2026-11-01T10:00:00+09:00", ""), ascii_folder("Mixed 한글", "2026-11-01", ""))
        self.assertTrue(ascii_folder("", None, "").startswith("post-00000000-"))

    def test_renamed_bundle_folder_is_the_same_page(self):
        # addendum 5: git mv of a Korean folder to an ASCII one must not look like a new post (no second page)
        slug = "스몰토크는-왜-중요한가"
        text = POST.replace("slug: hello", f"slug: {slug}").replace("draft: false", "draft: false\nnotion_id: PLACEHOLDER")
        self.repo.write(slug, text)
        self.repo.commit("korean")
        self.push([slug])
        page_id = next(p["id"] for p in self.client.pages.values() if engine.plain(p["properties"]["Slug"]) == slug)
        folder = self.repo.path / "content/posts" / slug
        (folder / "index.md").write_text(text.replace("PLACEHOLDER", page_id), encoding="utf-8")
        self.repo.commit("notion_id")
        self.push([slug])
        pages_before = len(self.client.pages)
        before = git(self.repo.path, "rev-parse", "HEAD")
        git(self.repo.path, "mv", f"content/posts/{slug}", "content/posts/post-20260515-abcd1234")
        moved = (self.repo.path / "content/posts/post-20260515-abcd1234/index.md")
        moved.write_text(moved.read_text().replace(f"slug: {slug}\n", f"url: /posts/{slug}/\n"), encoding="utf-8")
        after = self.repo.commit("ascii folder")
        slugs = engine.changed_slugs(self.repo.path, before, after)
        self.assertIn("post-20260515-abcd1234", slugs)
        results = {r.slug: r for r in self.push(slugs)}
        self.assertEqual(results["post-20260515-abcd1234"].action, "write")  # found by notion_id, rewritten once
        self.assertEqual(results["post-20260515-abcd1234"].detail, page_id)
        self.assertEqual(len(self.client.pages), pages_before)  # no duplicate page
        self.assertEqual(engine.plain(self.client.pages[page_id]["properties"]["Slug"]), "post-20260515-abcd1234")
        self.assertEqual([r.action for r in self.push(["post-20260515-abcd1234"])], ["same"])
        # bundle files are published under the page URL (url:), not the folder: Notion shows them from there
        page = self.client.pages[page_id]
        self.assertEqual(page["cover"]["external"]["url"],
                         f"{SITE}/posts/%EC%8A%A4%EB%AA%B0%ED%86%A0%ED%81%AC%EB%8A%94-%EC%99%9C-%EC%A4%91%EC%9A%94%ED%95%9C%EA%B0%80/cover.jpg")
        # pulling that page back maps the image URL to the bundle file again (no churn)
        self.assertEqual([r.action for r in self.pull()], ["bot"])

    def test_every_write_is_logged_before_a_later_failure(self):
        self.repo.write("second", POST.replace("slug: hello", "slug: second"))
        self.repo.commit("second")
        real_append, calls = self.io.append, []

        def append(block_id, children):
            calls.append(block_id)
            if len(calls) == 2:
                raise RuntimeError("Notion down")
            return real_append(block_id, children)
        self.io.append = append
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(RuntimeError):
            self.push(["hello", "second"])
        lines = out.getvalue().splitlines()
        self.assertTrue(lines[0].startswith("ssot push: writing hello"))
        self.assertTrue(lines[1].startswith("ssot push: create hello p"))
        self.assertTrue(lines[2].startswith("ssot push: writing second"))  # the page that failed is named too

    def test_notion_cover_change_comes_back(self):
        # BLOG-017 F4: only the page cover changed in Notion
        self.push()
        page_id = self.page()["id"]
        self.client.pages[page_id]["cover"] = {"type": "external", "external": {"url": "https://img.example/new.jpg"}}
        self.client.touch(page_id, "person")
        self.assertEqual([r.action for r in self.pull()], ["commit"])
        index = self.repo.index()
        self.assertIn("image: https://img.example/new.jpg", index)
        self.assertNotIn("relative: true", index)
        self.assertIn("hiddenInSingle: false", index)
        self.assertEqual([r.action for r in self.push()], ["same"])  # cover is in the hash both sides agree on
        self.assertEqual([r.action for r in self.pull()], ["bot"])

    def test_notion_file_cover_is_downloaded(self):
        self.push()
        page_id = self.page()["id"]
        signed = "https://prod-files-secure.s3.us-west-2.amazonaws.com/x/cover.png?X-Amz-Signature=abc"
        self.client.pages[page_id]["cover"] = {"type": "file", "file": {"url": signed}}
        self.client.touch(page_id, "person")
        self.assertEqual([r.action for r in self.pull(fetch=lambda url: (b"new-cover-bytes", "image/png"))], ["commit"])
        name = "cover-" + __import__("hashlib").sha256(b"new-cover-bytes").hexdigest()[:8] + ".png"
        self.assertEqual((self.repo.path / "content/posts/hello" / name).read_bytes(), b"new-cover-bytes")
        self.assertIn(f"image: {name}", self.repo.index())
        self.assertIn("relative: true", self.repo.index())
        self.assertNotIn("amazonaws", self.repo.index())
        # pushed back, Notion shows the bundle copy from the site; pulling that again changes nothing
        self.assertEqual([r.action for r in self.push()], ["same"])

    def test_unchanged_cover_causes_no_front_matter_churn(self):
        self.push()
        page_id = self.page()["id"]
        self.client.human_edit(page_id, edit_paragraph("끝 문단.", "끝 문단만 바꿈."))
        self.pull()
        self.assertIn('title: "시험 글"', self.repo.index())  # front matter kept byte for byte
        self.assertIn("  image: cover.jpg\n  relative: true\n", self.repo.index())

    def test_bot_edit_is_skipped(self):
        self.push()
        page_id = self.page()["id"]
        self.client.human_edit(page_id, edit_paragraph("끝 문단.", "다른 통합이 바꾼 문단."), editor="bot")
        self.assertEqual([r.action for r in self.pull()], ["bot"])
        self.assertNotIn("다른 통합이 바꾼 문단.", self.repo.index())
        self.assertEqual(len(self.repo.remote_log()), 1)

    def test_editor_type_without_user_information_capability(self):
        self.client.users_forbidden = True
        self.push()
        self.assertEqual([r.action for r in self.pull()], ["bot"])  # our own id (users/me) = bot
        self.client.human_edit(self.page()["id"], edit_paragraph("끝 문단.", "사람이 고친 문단."))
        self.io._user_types.clear()
        self.assertEqual([r.action for r in self.pull()], ["commit"])
        self.assertIn("사람이 고친 문단.", self.repo.index())

    def test_assume_person_hook_needs_a_page_id(self):
        self.push()
        page_id = self.page()["id"]
        self.client.human_edit(page_id, edit_paragraph("끝 문단.", "에이전트가 고친 문단."), editor="bot")
        with self.assertRaises(SystemExit):
            engine.plan_pull(self.io, DB, self.repo.path, SITE, assume_person=True)
        results, changes = engine.plan_pull(self.io, DB, self.repo.path, SITE, page_ids=[page_id], assume_person=True)
        self.assertEqual([r.action for r in results], ["commit"])
        engine.apply_pull(self.io, self.repo.path, changes, "main", now=self.client.now)
        self.assertIn("에이전트가 고친 문단.", self.repo.index())
        self.assertEqual([r.action for r in self.pull()], ["bot"])  # without the hook the stamp write is ours again

    def test_notion_file_image_is_downloaded_into_the_bundle(self):
        self.push()
        page_id = self.page()["id"]
        signed = "https://prod-files-secure.s3.us-west-2.amazonaws.com/x/new%20shot.png?X-Amz-Signature=abc"

        def add_image(blocks):
            blocks.append({"object": "block", "id": "img-0001-0000", "type": "image", "has_children": False,
                           "image": {"type": "file", "file": {"url": signed, "expiry_time": "2026-11-09T02:00:00Z"},
                                     "caption": read_form([{"text": {"content": "새 그림"}}])}})
        self.client.human_edit(page_id, add_image)
        fetched = []
        self.assertEqual([r.action for r in self.pull(fetch=lambda url: fetched.append(url) or (b"png-bytes", "image/png"))],
                         ["commit"])
        self.assertEqual(fetched, [signed])
        name = "notion-img00010000.png"  # notion-<block id without dashes, 12 chars max>
        self.assertEqual((self.repo.path / "content/posts/hello" / name).read_bytes(), b"png-bytes")
        self.assertIn(f"![새 그림]({name})", self.repo.index())
        self.assertNotIn("amazonaws", self.repo.index())  # no expiring URL in the repo
        self.assertIn(name, git(self.repo.remote, "show", "--stat", "--format=", "main"))

    def test_only_allowlist_and_dry_run_write_nothing(self):
        self.repo.write("other", POST.replace("slug: hello", "slug: other"))
        self.repo.commit("other")
        results = self.push(("hello", "other"), only={"hello"}, dry_run=True)
        self.assertEqual([(r.slug, r.action) for r in results], [("hello", "create"), ("other", "skip")])
        self.assertEqual(self.client.writes(), [])

    def test_two_pages_with_one_slug_stop(self):
        self.push()
        self.client.pages["dup"] = dict(self.page(), id="dup")
        self.repo.write("hello", POST.replace("끝 문단.", "바뀜."))
        with self.assertRaises(RuntimeError):
            self.push()

    def test_replace_children_reads_past_100(self):
        self.push()
        page_id = self.page()["id"]
        self.client._store_blocks(page_id, [{"type": "paragraph", "paragraph": {"rich_text": []}}] * 150)
        self.io.replace_children(page_id, md_to_blocks("하나\n\n둘"))
        self.assertEqual([engine.plain({"type": "rich_text", "rich_text": b["paragraph"]["rich_text"]})
                          for b in self.client.children[page_id]], ["하나", "둘"])

    def test_cli_needs_https_site_and_database(self):
        env = {k: v for k, v in os.environ.items() if k not in ("NOTION_DATABASE_ID_POSTS", "SSOT_SITE")}
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(cli(["push", "--repo", str(self.repo.path), "--site", "http://x"], io=self.io), 2)
            self.assertEqual(cli(["push", "--repo", str(self.repo.path), "--database", DB, "--site", SITE,
                                  "--add-sync-column", "--slug", "hello", "--dry-run"], io=self.io), 0)
        self.assertEqual(self.client.writes(), [])


if __name__ == "__main__":
    unittest.main()
