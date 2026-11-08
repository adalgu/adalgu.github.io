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
        if item.get("type") == "mention":  # Notion fills plain_text (the page title) and href itself
            page = (item["mention"].get("page") or {}).get("id")
            out.append({"type": "mention", "mention": item["mention"],
                        "plain_text": "연결된 쪽" if page else str((item["mention"].get("date") or {}).get("start", "")),
                        "href": "https://www.notion.so/" + page.replace("-", "") if page else None,
                        "annotations": {k: False for k in ("bold", "italic", "strikethrough", "underline", "code")}})
            continue
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
        self.fail_appends_after = None  # N = the (N+1)th append call fails

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
        stored_list = []
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
            stored_list.append(stored)
            if nested:
                self._store_blocks(stored["id"], nested)
        return stored_list

    @staticmethod
    def _nesting(blocks):
        return max([0] + [1 + FakeClient._nesting((b.get(b["type"]) or {}).get("children") or []) for b in blocks
                          if (b.get(b["type"]) or {}).get("children")])

    def _refuse(self, blocks):
        """What the real API refuses (addendum 9): more than two nested levels in one request, empty columns."""
        if self._nesting(blocks) > 2:
            raise RuntimeError("400 validation_error: nesting deeper than two levels")
        stack = list(blocks)
        while stack:
            b = stack.pop()
            data = b.get(b["type"]) or {}
            if b["type"] == "column" and not data.get("children"):
                raise RuntimeError("400 validation_error: column needs children")
            stack += data.get("children") or []

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
                self._refuse(body["children"])
                if self.fail_appends_after is not None:  # test hook: one append call falls over
                    if self.fail_appends_after <= 0:
                        self.fail_appends_after = None
                        raise RuntimeError("503 service_unavailable")
                    self.fail_appends_after -= 1
                stored = self._store_blocks(parts[1], copy.deepcopy(body["children"]))
                self.touch(self._owner(parts[1]))
                return {"results": stored}
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

    RICH_MD = ("앞 문단 [연결된 쪽](https://www.notion.so/a08d8d61be324e079dab548db6407849) 언급.\n\n"
               "<!-- notion-callout: icon=💡 color=gray_background -->\n> 알아 둘 것\n> 둘째 줄\n\n"
               "- [ ] 할 일 하나\n- [x] 끝낸 일\n\n"
               "<!-- notion-link-to-page: page_id=a08d8d61-be32-4e07-9dab-548db6407849 -->\n\n"
               "<!-- notion-columns -->\n\n<!-- notion-column width=0.5 -->\n\n왼쪽 문단\n\n- 왼쪽 목록\n\n"
               "<!-- notion-column width=0.5 -->\n\n오른쪽 문단\n\n<!-- /notion-columns -->\n\n뒤 문단.\n")

    def test_callout_todo_link_mention_columns_round_trip(self):
        # BLOG-017 addendum 8 (Anton round 7): these kinds used to vanish on the way back to Notion
        blocks = md_to_blocks(self.RICH_MD)
        self.assertEqual([b["type"] for b in blocks],
                         ["paragraph", "callout", "to_do", "to_do", "link_to_page", "column_list", "paragraph"])
        self.assertEqual(blocks[0]["paragraph"]["rich_text"][1]["type"], "mention")
        self.assertEqual(blocks[1]["callout"]["icon"], {"type": "emoji", "emoji": "💡"})
        self.assertEqual([b["to_do"]["checked"] for b in blocks[2:4]], [False, True])
        cols = blocks[5]["column_list"]["children"]
        self.assertEqual([[k["type"] for k in c["column"]["children"]] for c in cols], [["paragraph", "bulleted_list_item"], ["paragraph"]])
        client = FakeClient()
        client.pages["p"] = {"id": "p"}
        client._store_blocks("p", blocks)
        md = blocks_to_markdown(client.children["p"], client.children.get)
        self.assertEqual(md, self.RICH_MD)  # Notion -> Markdown gives the same text back
        counts = engine.block_kind_counts(md_to_blocks(md))
        self.assertEqual(counts, engine.notion_kind_counts(NotionIO(client), "p"))  # every kind, same number
        self.assertEqual(counts["mention:page"], 1)
        self.assertEqual(counts["column"], 2)
        # Notion also hands page mentions out as app.notion.com/p/<id> (seen on live pages)
        alt = md_to_blocks("[쪽](https://app.notion.com/p/6e1afcdae6484028a78af10c3041f82c) 보기")[0]["paragraph"]["rich_text"][0]
        self.assertEqual(alt["mention"]["page"]["id"], "6e1afcda-e648-4028-a78a-f10c3041f82c")
        bracketed = md_to_blocks("[[Notion] 노션과 도메인 연결하기](https://app.notion.com/p/736f0e70d77e447a9cb9a7b85b984c96) 끝")
        self.assertEqual(bracketed[0]["paragraph"]["rich_text"][0]["type"], "mention")  # title with [..] inside
        # a paragraph that is only a mention is content, not an empty spacer (counted on the write side too)
        self.assertEqual(engine.block_kind_counts(bracketed[:1]), {"paragraph": 1, "mention:page": 1, "@0:page>paragraph": 1})
        only = md_to_blocks("[쪽](https://app.notion.com/p/6e1afcdae6484028a78af10c3041f82c)")
        self.assertEqual(engine.block_kind_counts(only), {"paragraph": 1, "mention:page": 1, "@0:page>paragraph": 1})

    # ---- BLOG-017 addendum 9 (Anton r8) ----
    def _page_with(self, build):
        """push hello, then make its Notion body = build(page_id) as a bot edit; returns page id."""
        self.push()
        page_id = self.page()["id"]
        self.client.children[page_id] = []
        build(page_id)
        self.client.touch(page_id, "bot")
        return page_id

    def _tree(self, block_id, depth=0):
        out = []
        for b in self.client.children.get(block_id, []):
            data = b[b["type"]]
            extra = data.get("icon") if b["type"] == "callout" else data.get("checked") if b["type"] == "to_do" else ""
            out.append(("  " * depth) + b["type"] + (f" {extra}" if extra not in ("", None) else ""))
            out += self._tree(b["id"], depth + 1)
        return out

    def _repo_from_notion(self, page_id, extra="저장소 끝 줄."):
        md = blocks_to_markdown(self.client.children[page_id], self.client.children.get)
        head = POST.split("---", 2)
        self.repo.write("hello", "---" + head[1] + "---\n\n" + md + "\n" + extra + "\n")
        return md

    NESTED_MD = ("- 부모\n  - 자식\n\n- [ ] 할 일\n  - [x] 하위 할 일\n\n"
                 "<!-- notion-callout: icon=💡 color=default -->\n> 콜아웃\n  콜아웃 안 문단\n\n"
                 "<!-- notion-callout: icon_url=https://img.example/i.png color=blue_background -->\n> 외부 아이콘\n\n"
                 "> 인용\n  1. 인용 안 번호\n")

    def test_nested_children_and_external_icon_round_trip(self):
        page_id = self._page_with(lambda pid: self.client._store_blocks(pid, md_to_blocks(self.NESTED_MD)))
        before = self._tree(page_id)
        self.assertEqual(before, ["bulleted_list_item", "  bulleted_list_item", "to_do False", "  to_do True",
                                  "callout {'type': 'emoji', 'emoji': '💡'}", "  paragraph",
                                  "callout {'type': 'external', 'external': {'url': 'https://img.example/i.png'}}",
                                  "quote", "  numbered_list_item"])
        md = self._repo_from_notion(page_id)
        self.assertEqual(md, self.NESTED_MD)
        (result,) = self.push()
        self.assertEqual(result.action, "write")
        self.assertEqual(self._tree(page_id), before + ["paragraph"])  # same nesting, same icons, plus the new line

    def test_guard_counts_mentions_in_table_cells(self):
        date = {"type": "mention", "mention": {"type": "date", "date": {"start": "2026-11-09"}}}

        def build(pid):
            self.client._store_blocks(pid, [{"type": "table", "table": {"table_width": 2, "has_column_header": True, "has_row_header": False,
                                                                       "children": [{"type": "table_row", "table_row": {"cells": [rich("a"), rich("b")]}},
                                                                                    {"type": "table_row", "table_row": {"cells": [[date], rich("d")]}}]}}])
        page_id = self._page_with(build)
        self.client.children[self.client.children[page_id][0]["id"]][1]["table_row"]["cells"][0] = [
            {"type": "mention", "mention": date["mention"], "plain_text": "2026-11-09", "href": None, "annotations": {}}]
        self._repo_from_notion(page_id)
        writes = len(self.client.writes())
        (result,) = self.push()
        self.assertEqual(result.action, "skip")
        self.assertIn("mention:date:1→0", result.detail)
        self.assertEqual(len(self.client.writes()), writes)

    def test_guard_skips_a_structure_change_with_equal_kind_counts(self):
        page_id = self._page_with(lambda pid: self.client._store_blocks(pid, md_to_blocks("- 부모\n  - 자식\n")))
        self.repo.write("hello", POST.replace("끝 문단.", "- 부모\n- 자식"))  # same kinds, nesting gone
        writes = len(self.client.writes())
        (result,) = self.push()
        self.assertEqual(result.action, "skip")
        self.assertIn("@1:bulleted_list_item>bulleted_list_item:1→0", result.detail)
        self.assertEqual(len(self.client.writes()), writes)

    def test_bodies_notion_would_refuse_are_skipped_before_any_delete(self):
        for name, md, reason in (
                ("empty column", "<!-- notion-columns -->\n\n<!-- notion-column -->\n\n<!-- notion-column -->\n\n오른쪽\n\n<!-- /notion-columns -->\n", "empty column"),
                ("table in column", "<!-- notion-columns -->\n\n<!-- notion-column -->\n\n| h |\n| --- |\n| v |\n\n"
                                    "<!-- notion-column -->\n\n오른쪽\n\n<!-- /notion-columns -->\n", "nesting>2")):
            with self.subTest(name):
                self.setUp()
                self.push()
                page_id = self.page()["id"]
                before = self._tree(page_id)
                self.repo.write("hello", POST.replace("끝 문단.", "끝 문단.\n\n" + md))
                writes = len(self.client.writes())
                (result,) = self.push()
                self.assertEqual(result.action, "skip")
                self.assertIn(reason, result.detail)
                self.assertEqual(len(self.client.writes()), writes)  # nothing deleted, nothing written
                self.assertEqual(self._tree(page_id), before)

    def test_failed_append_puts_the_old_body_back(self):
        page_id = self._page_with(lambda pid: self.client._store_blocks(pid, md_to_blocks(self.NESTED_MD + "\n| a | b |\n| --- | --- |\n| 1 | 2 |\n")))
        before = self._tree(page_id)
        synced_before = engine.sync_state(self.client.pages[page_id])
        self.repo.write("hello", POST.replace("끝 문단.", "완전히 다른 본문.\n\n" + self.NESTED_MD + "\n| a | b |\n| --- | --- |\n| 1 | 2 |"))
        self.client.fail_appends_after = 0  # the next append dies after the old blocks are gone
        with self.assertRaises(RuntimeError):
            self.push()
        self.assertEqual(self._tree(page_id), before)  # old body back, nesting and icons included
        self.assertEqual(engine.sync_state(self.client.pages[page_id])[0], synced_before[0])  # SyncHash untouched

    def test_push_never_shrinks_a_notion_page(self):
        # the general guard: any kind fewer after the write = skip that page, Notion untouched, dry_run says so too
        self.push()
        page_id = self.page()["id"]

        self.client.human_edit(page_id, lambda blocks: self.client._store_blocks(page_id, md_to_blocks(self.RICH_MD)),
                               editor="bot")  # a bot edit: pull skips it, push must still not erase it
        self.repo.write("hello", POST.replace("끝 문단.", "저장소에서 바꾼 끝 문단."))
        writes = len(self.client.writes())
        for dry in (True, False):
            (result,) = self.push(dry_run=dry)
            self.assertEqual(result.action, "skip")
            self.assertTrue(result.detail.startswith("lossy "), result.detail)
            for kind in ("callout:1→0", "column:2→0", "column_list:1→0", "link_to_page:1→0", "mention:page:1→0", "to_do:2→0"):
                self.assertIn(kind, result.detail)
        self.assertEqual(len(self.client.writes()), writes)  # Notion writes 0
        # the same content written in Markdown with the notes goes through
        self.repo.write("hello", POST.replace("끝 문단.", "저장소에서 바꾼 끝 문단.\n\n" + self.RICH_MD))
        self.assertEqual([r.action for r in self.push()], ["write"])

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
