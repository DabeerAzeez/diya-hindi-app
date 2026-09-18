"""
Notion Client for Hindi Coach
Handles bidirectional synchronization, page renaming, and lesson summary publishing
to the student's 'Hindi Learning Plan' Notion workspace with full Markdown parsing
(bolding, italics, tables, LaTeX equations, and nested lists).
"""

import sys
import json
import re
import urllib.request
import argparse

sys.stdout.reconfigure(encoding='utf-8')

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
PARENT_PAGE_ID = "3ad85bc1d96280979536d9f70446ca04"
LESSONS_HEADING_ID = "3ae85bc1-d962-803d-8a50-f92d02ac5be1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def api_request(endpoint, method="GET", data=None):
    url = f"https://api.notion.com/v1/{endpoint}"
    encoded_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        raise RuntimeError(f"Notion API HTTP Error {e.code}: {err_msg}")
    except Exception as e:
        raise RuntimeError(f"Notion API Request Error: {e}")

def parse_inline_rich_text(text):
    """
    Parses a string of inline markdown into Notion rich_text objects.
    Supports **bold**, *italic*, `code`, and $inline math$.
    """
    if not text:
        return []

    pattern = re.compile(
        r'(\$(?:\\.|[^$])+\$'
        r'|\*\*\*(?:[^*]|\*(?!\*\*))+\*\*\*'
        r'|\*\*(?:[^*]|\*(?!\*))+\*\*'
        r'|\*[^*]+\*'
        r'|`[^`]+`)'
    )
    tokens = pattern.split(text)
    rich_text = []

    for token in tokens:
        if not token:
            continue
        # Inline Equation: $...$
        if token.startswith('$') and token.endswith('$') and len(token) >= 2:
            rich_text.append({
                "type": "equation",
                "equation": {"expression": token[1:-1].strip()}
            })
        # Bold + Italic: ***...***
        elif token.startswith('***') and token.endswith('***') and len(token) >= 6:
            rich_text.append({
                "type": "text",
                "text": {"content": token[3:-3]},
                "annotations": {
                    "bold": True,
                    "italic": True,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default"
                }
            })
        # Bold: **...**
        elif token.startswith('**') and token.endswith('**') and len(token) >= 4:
            rich_text.append({
                "type": "text",
                "text": {"content": token[2:-2]},
                "annotations": {
                    "bold": True,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default"
                }
            })
        # Italic: *...*
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            rich_text.append({
                "type": "text",
                "text": {"content": token[1:-1]},
                "annotations": {
                    "bold": False,
                    "italic": True,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default"
                }
            })
        # Inline Code: `...`
        elif token.startswith('`') and token.endswith('`') and len(token) >= 2:
            rich_text.append({
                "type": "text",
                "text": {"content": token[1:-1]},
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": True,
                    "color": "default"
                }
            })
        # Plain text
        else:
            rich_text.append({
                "type": "text",
                "text": {"content": token},
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default"
                }
            })
    return rich_text

def _split_table_row(row_str):
    s = row_str.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [cell.strip() for cell in s.split('|')]

def _is_table_separator(row_str):
    cells = _split_table_row(row_str)
    return all(re.match(r'^:?-+:?$', c) for c in cells if c)

def markdown_to_notion_blocks(md_text):
    """
    Converts complete lesson markdown into Notion block JSON structures.
    Supports headings, KaTeX display equations, native tables, blockquotes,
    dividers, numbered/bullet lists, and indented child answers.
    """
    lines = md_text.splitlines()
    blocks = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Blank line
        if not stripped:
            i += 1
            continue

        # Horizontal Rule
        if re.match(r'^(?:---|\*\*\*|___)$', stripped):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # Display Math: $$ ... $$
        if stripped.startswith('$$'):
            expr_lines = []
            if stripped.endswith('$$') and len(stripped) > 4:
                expr = stripped[2:-2].strip()
                i += 1
            else:
                expr_lines.append(stripped[2:])
                i += 1
                while i < n and not lines[i].strip().endswith('$$'):
                    expr_lines.append(lines[i].strip())
                    i += 1
                if i < n:
                    expr_lines.append(lines[i].strip()[:-2])
                    i += 1
                expr = " ".join(expr_lines).strip()

            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "equation",
                        "equation": {"expression": expr}
                    }]
                }
            })
            continue

        # Headings
        if stripped.startswith('# ') and not stripped.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": parse_inline_rich_text(stripped[2:].strip())}
            })
            i += 1
            continue
        if stripped.startswith('## ') and not stripped.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": parse_inline_rich_text(stripped[3:].strip())}
            })
            i += 1
            continue
        if stripped.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_inline_rich_text(stripped[4:].strip())}
            })
            i += 1
            continue

        # Blockquote / Tip (> ...)
        if stripped.startswith('> '):
            quote_text = stripped[2:].strip()
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": parse_inline_rich_text(quote_text)}
            })
            i += 1
            continue

        # Markdown Table (| Col 1 | Col 2 |)
        if stripped.startswith('|') and '|' in stripped[1:]:
            table_lines = []
            while i < n and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 2 and _is_table_separator(table_lines[1]):
                headers = _split_table_row(table_lines[0])
                table_width = len(headers)
                data_rows = table_lines[2:]
            else:
                headers = _split_table_row(table_lines[0])
                table_width = len(headers)
                data_rows = table_lines[1:]

            table_row_blocks = []
            # Header row
            table_row_blocks.append({
                "type": "table_row",
                "table_row": {
                    "cells": [parse_inline_rich_text(h) for h in headers]
                }
            })
            # Data rows
            for d_row in data_rows:
                row_cells = _split_table_row(d_row)
                if len(row_cells) < table_width:
                    row_cells.extend([''] * (table_width - len(row_cells)))
                else:
                    row_cells = row_cells[:table_width]
                table_row_blocks.append({
                    "type": "table_row",
                    "table_row": {
                        "cells": [parse_inline_rich_text(c) for c in row_cells]
                    }
                })

            blocks.append({
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": table_width,
                    "has_column_header": True,
                    "has_row_header": False,
                    "children": table_row_blocks
                }
            })
            continue

        # Numbered List item (e.g. 1. Question)
        num_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if num_match:
            item_text = num_match.group(2)
            i += 1
            children = []
            while i < n and (lines[i].startswith('   ') or lines[i].startswith('\t') or lines[i].startswith('    ')):
                sub_stripped = lines[i].strip()
                if sub_stripped:
                    sub_cleaned = re.sub(r'</?small>', '', sub_stripped)
                    if sub_cleaned.startswith('- ') or sub_cleaned.startswith('* '):
                        sub_text = sub_cleaned[2:].strip()
                    else:
                        sub_text = sub_cleaned
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": parse_inline_rich_text(sub_text)}
                    })
                i += 1

            block = {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_inline_rich_text(item_text)}
            }
            if children:
                block["numbered_list_item"]["children"] = children
            blocks.append(block)
            continue

        # Bulleted List item (e.g. - item or * item)
        bullet_match = re.match(r'^(?:-|\*)\s+(.*)$', stripped)
        if bullet_match:
            item_text = bullet_match.group(1)
            i += 1
            children = []
            while i < n and (lines[i].startswith('   ') or lines[i].startswith('\t') or lines[i].startswith('    ')):
                sub_stripped = lines[i].strip()
                if sub_stripped:
                    sub_cleaned = re.sub(r'</?small>', '', sub_stripped)
                    if sub_cleaned.startswith('- ') or sub_cleaned.startswith('* '):
                        sub_text = sub_cleaned[2:].strip()
                    else:
                        sub_text = sub_cleaned
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": parse_inline_rich_text(sub_text)}
                    })
                i += 1

            block = {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_inline_rich_text(item_text)}
            }
            if children:
                block["bulleted_list_item"]["children"] = children
            blocks.append(block)
            continue

        # Default: Normal Paragraph
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": parse_inline_rich_text(stripped)}
        })
        i += 1

    return blocks

def rename_page(page_id, new_title):
    """Updates the title property of a Notion page."""
    payload = {
        "properties": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": new_title}
                }
            ]
        }
    }
    res = api_request(f"pages/{page_id}", method="PATCH", data=payload)
    return res.get("id")

def get_child_pages(parent_id=PARENT_PAGE_ID):
    """Lists all child blocks of the parent page."""
    results = []
    cursor = None
    while True:
        url = f"blocks/{parent_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        res = api_request(url, method="GET")
        results.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    return results

def create_lesson_page(title, blocks, parent_id=PARENT_PAGE_ID):
    """Creates a new child page and appends any extra blocks beyond the 100-block limit."""
    payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": title}
                }
            ]
        },
        "children": blocks[:100]
    }
    res = api_request("pages", method="POST", data=payload)
    page_id = res.get("id")

    # If there are more than 100 blocks, batch append the rest
    if len(blocks) > 100:
        for i in range(100, len(blocks), 100):
            chunk = blocks[i:i+100]
            api_request(f"blocks/{page_id}/children", method="PATCH", data={"children": chunk})

    return page_id

def create_lesson_from_markdown(title, md_content, parent_id=PARENT_PAGE_ID):
    """Parses raw Markdown and publishes a fully styled Notion page."""
    blocks = markdown_to_notion_blocks(md_content)
    return create_lesson_page(title, blocks, parent_id=parent_id)

# Confirmed Mapping of Existing Notion Lessons to Clean A0/A1 codes
LESSON_RENAME_MAP = {
    "3ca85bc1-d962-806b-ba4b-c1abdfd5f710": "Lesson A0-00: Pronunciation & Hindi Phonetics",
    "3af85bc1-d962-80a3-8645-e0fa15f0c876": "Lesson A0-01: Pronouns, 'To Be' Verbs & Hinglish Foundations",
    "3af85bc1-d962-80eb-8de8-de1fce68ed1b": "Lesson A0-02: Present Continuous & Present Habitual (Doing vs. Does)",
    "3af85bc1-d962-80b0-ba6f-f923bbe8c4dc": "Lesson A0-03: Basic Connectors & Postpositions",
    "3b085bc1-d962-802a-9feb-d8629ef11a2a": "Lesson A0-04: Can and Want",
    "3b085bc1-d962-806f-b9cc-d8321d6c55e9": "Lesson A0-05: The Oblique Shift & Core Postpositions",
    "3b685bc1-d962-808f-aac4-f8f51b6ecab0": "Lesson A0-06: Simple Past Tense & Completed Actions",
    "3b785bc1-d962-80c0-9028-d6ef60e0acf7": "Lesson A0-07: Gender Suffixes & Agreement Rules",
    "3b785bc1-d962-80b2-bf0a-dcb649a3332e": "Lesson A0-08: Simple Future Tense & Expressing Plans",
    "3c785bc1-d962-8024-8061-d4efb89ee749": "Lesson A1-01: Imperatives & Giving Directions",
    "3c885bc1-d962-800c-a986-d6bdc91db0ee": "Lesson A1-02: Possessives, Relationships & Family",
    "3ca85bc1-d962-80a8-960f-f048dfd78b35": "Lesson A1-03: Multiple Uses of 'Ki' vs. 'Kaa/Ke/Kee'",
    "3c885bc1-d962-8025-95d8-e70281942b0b": "Lesson A1-04: Obligation, Compulsion & Permission",
    "3ce85bc1-d962-80c5-9e08-eb0d882b1bbe": "Lesson A1-04.5: Postpositions & Oblique Case Consolidation",
    "3ce85bc1-d962-8073-9c24-e3884295683c": "Lesson A1-05: Habitual Past Tense & Past Continuous Tense",
    "3cf85bc1-d962-8060-9a2d-d06f15b2b3a4": "Lesson A1-06: Communication Verbs (Bolna, Kehna, Bataana, Baat Karna)",
    "3d685bc1-d962-8150-9cea-d70973fc581f": "Lesson A1-07: Quantifiers, Numbers, Shopping & Bargaining"
}

def execute_renames():
    """Batch renames all existing lesson pages on Notion."""
    print("Executing batch rename of Notion lesson pages...")
    for page_id, new_title in LESSON_RENAME_MAP.items():
        try:
            rename_page(page_id, new_title)
            print(f"✅ Renamed [{page_id}] -> {new_title}")
        except Exception as e:
            print(f"❌ Failed to rename [{page_id}]: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notion Sync CLI for Hindi Coach")
    parser.add_argument("--rename-all", action="store_true", help="Batch rename existing lesson pages")
    parser.add_argument("--sync-file", type=str, help="Path to markdown file to publish as a lesson page")
    parser.add_argument("--title", type=str, help="Title for the newly created lesson page")
    args = parser.parse_args()

    if args.rename_all:
        execute_renames()
    elif args.sync_file and args.title:
        with open(args.sync_file, 'r', encoding='utf-8') as f:
            content = f.read()
        page_id = create_lesson_from_markdown(args.title, content)
        print(f"✅ Successfully published '{args.title}' to Notion! Page ID: {page_id}")
    else:
        parser.print_help()
