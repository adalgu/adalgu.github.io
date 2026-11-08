"""Markdown <-> Notion blocks, written as inverses of each other.

md_to_blocks(blocks_to_markdown(x)) and blocks_to_markdown(md_to_blocks(md)) keep the text the engine itself
wrote, so a pull of a page nobody touched gives back the same bundle (same hash, nothing to commit).
Covered: paragraphs (line breaks kept), # / ## / ###, - and 1. lists, ``` code, > quotes, --- dividers,
![alt](src) images, | pipe | tables | (Notion table + table_row, header row kept; BLOG-017 addendum 6),
**bold** *italic* ~~strike~~ `code` [links](url). Anything else Notion holds (toggles,
tables, callouts, nested children) is rendered the way src/render.py does, one way only.
"""
import re

TEXT_LIMIT = 2000  # characters per Notion rich_text item
CODE_LANGUAGES = {
    "bash", "c", "c++", "css", "go", "html", "java", "javascript", "json", "kotlin", "markdown", "python",
    "ruby", "rust", "shell", "sql", "swift", "typescript", "yaml",
}
INLINE = re.compile(r"\*\*(.+?)\*\*|~~(.+?)~~|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|(?<![*\w])\*([^*\s][^*]*?)\*(?!\*)")
IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
LIST_TYPES = ("bulleted_list_item", "numbered_list_item")
# Notion table header settings that a pipe table cannot say (BLOG-017 addendum 7): written on the line right above
# the table only when they differ from what a pipe table means (column header on, row header off). Hugo keeps an
# HTML comment out of sight.
TABLE_NOTE = re.compile(r"^<!--\s*notion-table:\s*column_header=(true|false)\s+row_header=(true|false)\s*-->$")
TABLE_SEP = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")


# ---------- Markdown -> blocks ----------

def rich_text(text):
    out = []

    def push(content, link=None, **marks):
        for at in range(0, len(content), TEXT_LIMIT):
            item = {"type": "text", "text": {"content": content[at:at + TEXT_LIMIT]}}
            if link:
                item["text"]["link"] = {"url": link}
            on = {k: True for k, v in marks.items() if v}
            if on:
                item["annotations"] = on
            out.append(item)

    pos = 0
    for match in INLINE.finditer(text):
        if match.start() > pos:
            push(text[pos:match.start()])
        bold, strike, code, label, url, italic = match.groups()
        if bold is not None:
            push(bold, bold=True)
        elif strike is not None:
            push(strike, strikethrough=True)
        elif code is not None:
            push(code, code=True)
        elif label is not None:
            push(label, link=url)
        else:
            push(italic, italic=True)
        pos = match.end()
    if pos < len(text):
        push(text[pos:])
    return out


def _text_block(kind, text):
    return {"object": "block", "type": kind, kind: {"rich_text": rich_text(text)}}


def _chunks(text):
    return [text[at:at + TEXT_LIMIT] for at in range(0, len(text), TEXT_LIMIT)] or [""]


def table_cells(line):
    """'| a | b \\| c |' -> ['a', 'b | c'] — split on pipes that are not escaped, outer pipes dropped."""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", body)]


def table_note(column_header, row_header):
    return f"<!-- notion-table: column_header={str(bool(column_header)).lower()} row_header={str(bool(row_header)).lower()} -->"


def table_block(lines, flags=None):
    """Pipe-table lines -> one Notion table block with its table_row children (cells rich text).
    flags = (column_header, row_header) from a notion-table note above the table; without one, a separator row
    means a column header and there is no row header."""
    rows = [table_cells(line) for line in lines]
    separator = len(rows) > 1 and bool(TABLE_SEP.match(lines[1].strip()))
    if separator:
        rows = [rows[0]] + rows[2:]
    header, row_header = flags if flags else (separator, False)
    width = max(len(r) for r in rows)
    children = [{"object": "block", "type": "table_row",
                 "table_row": {"cells": [rich_text(c) for c in row + [""] * (width - len(row))]}} for row in rows]
    return {"object": "block", "type": "table",
            "table": {"table_width": width, "has_column_header": header, "has_row_header": row_header, "children": children}}


def md_to_blocks(markdown, image_url=lambda src: src):
    """image_url(src) -> absolute https URL Notion can show (bundle files live on the site)."""
    blocks, para, lines = [], [], markdown.splitlines()
    table_flags = None

    def flush():
        if para:
            blocks.append(_text_block("paragraph", "\n".join(para)))
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            language = stripped[3:].strip().lower()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            blocks.append({"object": "block", "type": "code",
                           "code": {"rich_text": [{"type": "text", "text": {"content": c}} for c in _chunks("\n".join(code))],
                                    "language": language if language in CODE_LANGUAGES else "plain text"}})
        elif not stripped:
            flush()
        elif (note := TABLE_NOTE.match(stripped)) and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            flush()
            table_flags = (note.group(1) == "true", note.group(2) == "true")  # belongs to the table on the next line
        elif stripped.startswith("|") and stripped.count("|") >= 2:
            flush()
            rows = [stripped]
            while i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
                i += 1
                rows.append(lines[i].strip())
            blocks.append(table_block(rows, table_flags))
            table_flags = None
        elif m := re.match(r"(#{1,6})\s+(.*)", stripped):
            flush()
            blocks.append(_text_block(f"heading_{min(len(m.group(1)), 3)}", m.group(2)))
        elif re.fullmatch(r"(-{3,}|\*{3,})", stripped):
            flush()
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif (m := IMAGE.fullmatch(stripped)):
            flush()
            alt, src = m.groups()
            image = {"type": "external", "external": {"url": image_url(src)}}
            if alt:
                image["caption"] = rich_text(alt)
            blocks.append({"object": "block", "type": "image", "image": image})
        elif m := re.match(r"[-*+]\s+(.*)", stripped):
            flush()
            blocks.append(_text_block("bulleted_list_item", m.group(1)))
        elif m := re.match(r"\d+[.)]\s+(.*)", stripped):
            flush()
            blocks.append(_text_block("numbered_list_item", m.group(1)))
        elif stripped.startswith(">"):
            flush()
            quote = [stripped[1:].strip()]
            while i + 1 < len(lines) and lines[i + 1].strip().startswith(">"):
                i += 1
                quote.append(lines[i].strip()[1:].strip())
            blocks.append(_text_block("quote", "\n".join(quote)))
        else:
            para.append(stripped)
        i += 1
    flush()
    return blocks


# ---------- blocks -> Markdown ----------

def text_of(items):
    out = ""
    for item in items or []:
        content = item.get("plain_text")
        if content is None:
            content = (item.get("text") or {}).get("content", "")
        marks = item.get("annotations") or {}
        if marks.get("code"):
            content = f"`{content}`"
        if marks.get("italic"):
            content = f"*{content}*"
        if marks.get("bold"):
            content = f"**{content}**"
        if marks.get("strikethrough"):
            content = f"~~{content}~~"
        link = item.get("href") or ((item.get("text") or {}).get("link") or {}).get("url")
        if link:
            content = f"[{content}]({link})"
        out += content
    return out


def blocks_to_markdown(blocks, children_of=lambda block_id: [], image_src=None):
    """image_src(block) -> path or URL to write in ![alt](...) (downloads Notion file images)."""
    parts = []  # (kind, text)
    number = 0
    for block in blocks:
        kind = block.get("type")
        data = block.get(kind) or {}
        number = number + 1 if kind == "numbered_list_item" else 0
        if kind == "paragraph":
            text = text_of(data.get("rich_text"))
            if not text:
                continue
        elif kind in ("heading_1", "heading_2", "heading_3"):
            text = "#" * int(kind[-1]) + " " + text_of(data.get("rich_text"))
        elif kind == "bulleted_list_item":
            text = "- " + text_of(data.get("rich_text"))
        elif kind == "numbered_list_item":
            text = f"{number}. " + text_of(data.get("rich_text"))
        elif kind == "to_do":
            text = ("- [x] " if data.get("checked") else "- [ ] ") + text_of(data.get("rich_text"))
        elif kind == "code":
            language = data.get("language") or ""
            text = f"```{'' if language == 'plain text' else language}\n{text_of_plain(data.get('rich_text'))}\n```"
        elif kind == "quote":
            text = "\n".join("> " + line for line in text_of(data.get("rich_text")).split("\n"))
        elif kind == "divider":
            text = "---"
        elif kind == "image":
            src = image_src(block) if image_src else (data.get(data.get("type")) or {}).get("url", "")
            text = f"![{text_of_plain(data.get('caption'))}]({src})"
        elif kind == "callout":
            text = "> " + text_of(data.get("rich_text"))
        elif kind == "toggle":
            inner = blocks_to_markdown(children_of(block["id"]), children_of, image_src) if block.get("has_children") else ""
            text = f"<details>\n<summary>{text_of(data.get('rich_text'))}</summary>\n\n{inner}\n</details>"
        elif kind == "table":
            text = _table(children_of(block["id"])) if block.get("has_children") else ""
            flags = (bool(data.get("has_column_header")), bool(data.get("has_row_header")))
            if text and flags != (True, False):  # what a plain pipe table means; anything else is kept in a note
                text = table_note(*flags) + "\n" + text
        else:
            continue
        if block.get("has_children") and kind not in ("toggle", "table"):
            inner = blocks_to_markdown(children_of(block["id"]), children_of, image_src)
            if inner:
                text += "\n" + "\n".join("  " + line if line else line for line in inner.split("\n"))
        parts.append((kind, text))
    out = ""
    for index, (kind, text) in enumerate(parts):
        out += text
        if index + 1 < len(parts):
            same_list = kind in LIST_TYPES and parts[index + 1][0] == kind
            out += "\n" if same_list else "\n\n"
    return out + "\n" if out else ""


def text_of_plain(items):
    return "".join(i.get("plain_text") if i.get("plain_text") is not None else (i.get("text") or {}).get("content", "")
                   for i in items or [])


def _table(rows):
    lines = []
    for index, row in enumerate(rows):
        cells = [text_of(cell).replace("|", "\\|") for cell in (row.get("table_row") or {}).get("cells", [])]
        lines.append("| " + " | ".join(cells) + " |")
        if index == 0:
            lines.append("| " + " | ".join("---" for _ in cells) + " |")
    return "\n".join(lines)
