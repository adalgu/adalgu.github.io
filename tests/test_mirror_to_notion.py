"""BL-003 Hugo → Notion 거울: 가짜 Notion 클라이언트(네트워크 0)로 slug upsert·안전장치 확인."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "mirror_to_notion", Path(__file__).resolve().parent.parent / "scripts" / "mirror_to_notion.py")
mirror = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mirror)

SCHEMA = {"Name": "title", "Slug": "rich_text", "Date": "date", "Tags": "multi_select", "Category": "select",
          "Description": "rich_text", "Source": "select", "isPublished": "checkbox", "skipRendering": "checkbox"}
POST = """---
title: "시험 글"
date: 2026-11-01T14:00:00+09:00
slug: hello-hugo
description: "설명"
tags: ["시험", "hugo"]
categories: ["메모"]
draft: {draft}
---

첫 문단 **굵게** 와 [링크](https://gunn.kim/).

## 소제목

- 하나
"""


class FakeNotion:
    """pages 를 메모리에 두고 notion_client.Client 와 같은 이름으로 부른다."""

    def __init__(self, schema=SCHEMA, pages=None):
        self.schema, self.store, self.calls = schema, list(pages or []), []
        outer = self

        class Databases:
            def retrieve(self, database_id):
                return {"properties": {k: {"type": v} for k, v in outer.schema.items()}}

            def query(self, database_id, filter):
                slug = filter["rich_text"]["equals"]
                return {"results": [p for p in outer.store if mirror._plain(p["properties"].get("Slug")) == slug]}

        class Pages:
            def create(self, parent, properties, children=()):
                outer.calls.append("create")
                page = {"id": f"page-{len(outer.store) + 1}", "properties": outer._stored(properties),
                        "children": list(children)}
                outer.store.append(page)
                outer.add_blocks(page["id"], children)
                return page

            def update(self, page_id, properties):
                outer.calls.append("update")
                page = next(p for p in outer.store if p["id"] == page_id)
                page["properties"].update(outer._stored(properties))
                return page

        class Children:
            # Notion 처럼 한 번에 최대 100개, has_more/next_cursor(다음 블록 id)로 넘긴다
            def list(self, block_id, page_size=100, start_cursor=None):
                blocks = outer.body.get(block_id, [])
                at = next((i for i, b in enumerate(blocks) if b["id"] == start_cursor), 0) if start_cursor else 0
                size = min(page_size, 100)
                more = at + size < len(blocks)
                return {"results": blocks[at:at + size], "has_more": more,
                        "next_cursor": blocks[at + size]["id"] if more else None}

            def append(self, block_id, children):
                outer.calls.append("append")
                outer.add_blocks(block_id, children)

        def delete(block_id):
            outer.calls.append("delete")
            for blocks in outer.body.values():
                blocks[:] = [b for b in blocks if b["id"] != block_id]

        self.body, self._block_seq = {}, 0
        self.databases, self.pages = Databases(), Pages()
        self.blocks = type("Blocks", (), {"children": Children(), "delete": staticmethod(delete)})()

    def add_blocks(self, page_id, children):
        for child in children:
            self._block_seq += 1
            self.body.setdefault(page_id, []).append({"id": f"b{self._block_seq}", **child})

    @staticmethod
    def _stored(properties):
        out = {}
        for name, value in properties.items():
            kind = next(iter(value))
            if kind in ("rich_text", "title"):
                out[name] = {"type": kind, kind: [{"plain_text": t["text"]["content"]} for t in value[kind]]}
            else:
                out[name] = {"type": kind, kind: value[kind]}
        return out


def fake(schema=SCHEMA, pages=None):
    return FakeNotion(schema, pages)


def store(client):
    return client.store


class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.posts = Path(self.tmp.name)
        self.write("hello-hugo", "false")

    def write(self, slug, draft):
        (self.posts / slug).mkdir(exist_ok=True)
        (self.posts / slug / "index.md").write_text(POST.format(draft=draft).replace("hello-hugo", slug), encoding="utf-8")

    def run_main(self, client, *extra):
        return mirror.main(["--posts-dir", str(self.posts), "--database", "db", *extra], client=client)

    def test_two_runs_one_page(self):
        client = fake()
        self.assertEqual(self.run_main(client), 0)
        self.assertEqual(self.run_main(client), 0)
        self.assertEqual(client.calls.count("create"), 1)
        self.assertEqual(client.calls.count("update"), 1)
        self.assertEqual(len(store(client)), 1)
        props = store(client)[0]["properties"]
        self.assertEqual(props["Source"]["select"], {"name": "hugo"})
        self.assertTrue(props["skipRendering"]["checkbox"])
        self.assertTrue(props["isPublished"]["checkbox"])
        self.assertEqual([t["name"] for t in props["Tags"]["multi_select"]], ["시험", "hugo"])
        self.assertNotIn("delete", client.calls)  # 기본은 Notion 쪽 지우기 0

    def test_body_blocks(self):
        client = fake()
        self.run_main(client)
        kinds = [b["type"] for b in store(client)[0]["children"]]
        self.assertEqual(kinds, ["paragraph", "heading_2", "bulleted_list_item"])
        texts = store(client)[0]["children"][0]["paragraph"]["rich_text"]
        self.assertEqual([t.get("annotations", {}).get("bold", False) for t in texts], [False, True, False, False, False])
        self.assertEqual(texts[3]["text"]["link"], {"url": "https://gunn.kim/"})

    def test_drafts_skip_unless_test(self):
        self.write("draft-post", "true")
        client = fake()
        self.run_main(client)
        self.assertEqual(len(store(client)), 1)
        self.run_main(client, "--test", "--only", "draft-post")
        self.assertEqual(len(store(client)), 2)
        self.assertFalse(store(client)[1]["properties"]["isPublished"]["checkbox"])

    def test_old_notion_page_with_same_slug_untouched(self):
        old = {"id": "old", "properties": {"Slug": {"type": "rich_text", "rich_text": [{"plain_text": "hello-hugo"}]},
                                           "Source": {"type": "select", "select": None}}}
        client = fake(pages=[old])
        self.assertEqual(self.run_main(client), 1)
        self.assertEqual(client.calls, [])
        self.assertEqual(len(store(client)), 1)

    def test_missing_source_column_stops(self):
        schema = {k: v for k, v in SCHEMA.items() if k != "Source"}
        client = fake(schema)
        self.assertEqual(self.run_main(client), 2)
        self.assertEqual(client.calls, [])
        self.assertEqual(self.run_main(client, "--allow-no-source-column"), 0)
        self.assertEqual(self.run_main(client, "--allow-no-source-column"), 0)
        self.assertEqual(client.calls.count("create"), 1)
        self.assertNotIn("Source", store(client)[0]["properties"])

    def test_dry_run_writes_nothing(self):
        client = fake()
        self.assertEqual(self.run_main(client, "--dry-run"), 0)
        self.assertEqual(client.calls, [])

    def test_replace_body_clears_more_than_one_page_of_blocks(self):
        # BLOG-011 보탬 1(리차드 실측): 옛 본문 103블록에 --replace-body → 첫 100개만 지워 옛 3블록이 맨 앞에 남았다
        client = fake()
        self.assertEqual(self.run_main(client), 0)
        page_id = store(client)[0]["id"]
        new_body = [{k: v for k, v in b.items() if k != "id"} for b in client.body[page_id]]
        client.body[page_id] = []
        client.add_blocks(page_id, [{"type": "paragraph", "old": n} for n in range(105)])
        self.assertEqual(len(mirror._child_ids(client, page_id)), 105)  # 100개 넘는 쪽도 한 번에 끝까지 읽음
        self.assertEqual(self.run_main(client, "--replace-body"), 0)
        self.assertEqual(client.calls.count("delete"), 105)
        body = client.body[page_id]
        self.assertEqual([b for b in body if "old" in b], [])  # 옛 블록 0
        self.assertEqual([{k: v for k, v in b.items() if k != "id"} for b in body], new_body)  # 새 본문만, 그 순서로

    def test_replace_body_stops_if_old_blocks_remain(self):
        client = fake()
        self.assertEqual(self.run_main(client), 0)
        page_id = store(client)[0]["id"]
        client.blocks.delete = staticmethod(lambda block_id: client.calls.append("delete"))  # 지워지지 않는 쪽
        with self.assertRaises(RuntimeError):
            mirror._clear_children(client, page_id)
        self.assertEqual(client.calls.count("delete"), mirror.CLEAR_ROUNDS * len(client.body[page_id]))


if __name__ == "__main__":
    unittest.main()
