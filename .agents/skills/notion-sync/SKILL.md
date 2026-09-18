---
name: notion-sync
description: Synchronize lesson summaries, vocabulary notes, and page titles directly to the student's Hindi Learning Plan Notion workspace via Notion REST API.
---

# Notion Sync (`/notion-sync`)

Use this skill whenever publishing a completed lesson summary, synchronizing new notes, or adjusting lesson titles on the student's Notion page.

## Configuration & Credentials
- **Parent Page ID:** `3ad85bc1d96280979536d9f70446ca04` ("Hindi Learning Plan")
- **Lessons Section ID:** `3ae85bc1-d962-803d-8a50-f92d02ac5be1` (`🧑‍🏫 Lessons`)
- **Helper Script:** [scripts/notion_client.py](./scripts/notion_client.py)

## Workflows

### 1. Publishing a Completed Lesson Summary
When a lesson is concluded with `/lesson`:
1. Format the content according to `lesson_summary_template.md` (Summary, LaTeX formulas, Lesson core, Dialogue Example, Quiz with indented answers).
2. Call `notion_client.create_lesson_from_markdown(title, md_content)` or run:
   ```bash
   python ".agents/skills/notion-sync/scripts/notion_client.py" --title "Lesson Title" --sync-file "path/to/lesson.md"
   ```
   This automatically converts markdown tables into native Notion `table`/`table_row` blocks, tokenizes `**bold**`, `*italic*`, and `` `code` `` into `rich_text` annotations, preserves LaTeX equations, and indents quiz answers.
3. Confirm the live Notion page URL to the student.

### 2. Renaming Pages
To rename any lesson or keep titles harmonized with the master curriculum:
- Run:
  ```bash
  python ".agents/skills/notion-sync/scripts/notion_client.py" --rename-all
  ```
