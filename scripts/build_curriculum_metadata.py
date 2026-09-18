"""
Build curriculum.json metadata for lessons-dashboard
Parses hindi_curriculum_a0_to_a2.md and memory/progress.json
"""

import os
import re
import json

def parse_curriculum():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    curriculum_path = os.path.join(base_dir, "hindi_curriculum_a0_to_a2.md")
    progress_path = os.path.join(base_dir, "memory", "progress.json")
    out_dir = os.path.join(base_dir, "lessons-dashboard", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "curriculum.json")

    with open(progress_path, "r", encoding="utf-8") as f:
        progress = json.load(f)

    current_code = progress["learning_strategy"]["current_lesson_code"]
    completed_codes = {item["code"] for item in progress.get("completed_lessons", [])}
    notion_parent_id = progress["learning_strategy"]["notion"]["parent_page_id"]
    notion_base_url = f"https://www.notion.so/{notion_parent_id}"

    with open(curriculum_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by level sections
    lessons = []
    current_level = "A0"
    current_level_name = "Level A0: Absolute Beginner (Foundations)"

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("## 🟢 Level A0"):
            current_level = "A0"
            current_level_name = "Level A0: Absolute Beginner (Foundations)"
        elif line.startswith("## 🟡 Level A1"):
            current_level = "A1"
            current_level_name = "Level A1: Elementary Spoken Hindi"
        elif line.startswith("## 🔴 Level A2"):
            current_level = "A2"
            current_level_name = "Level A2: Pre-Intermediate Spoken Hindi"
        elif line.startswith("## 🔵 Level B1"):
            current_level = "B1"
            current_level_name = "Level B1: Intermediate Spoken Hindi"
        elif line.startswith("### Lesson "):
            # e.g. "### Lesson A0-01: Pronouns, \"To Be\" Verbs & Hinglish Foundations"
            match = re.match(r'### Lesson\s+([A-Z0-9\-]+):\s*(.*)', line)
            if match:
                code = match.group(1).strip()
                raw_title = match.group(2).strip()
                # Remove any marker like 🎯 (Current Active Lesson)
                title = re.sub(r'🎯\s*\(Current Active Lesson\)', '', raw_title).strip()
                title = title.replace('"', '').strip()

                # Collect bullet points
                bullets = []
                formulas = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("### ") and not lines[i].strip().startswith("## "):
                    b_line = lines[i].strip()
                    if b_line.startswith("- "):
                        clean_b = b_line[2:].strip()
                        bullets.append(clean_b)
                    elif b_line.startswith("  - "):
                        clean_sub = b_line[4:].strip()
                        bullets.append(clean_sub)
                    i += 1
                
                # Derive formulas / key patterns from bullets
                for b in bullets:
                    if "Formula" in b or "Structure" in b or "Verb stem" in b or "Verb root" in b or "->" in b or "→" in b:
                        formulas.append(b)

                lessons.append({
                    "code": code,
                    "title": title,
                    "level": current_level,
                    "level_name": current_level_name,
                    "summary": bullets,
                    "key_formulas": formulas,
                    "is_completed": code in completed_codes,
                    "is_active": code == current_code,
                    "notion_url": notion_base_url
                })
                continue
        i += 1

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(lessons, f, indent=2, ensure_ascii=False)

    js_file = os.path.join(out_dir, "curriculum_data.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write("window.CURRICULUM_DATA = " + json.dumps(lessons, indent=2, ensure_ascii=False) + ";\n")

    print(f"Extracted {len(lessons)} lessons into {out_file} and {js_file}")
    return lessons

if __name__ == "__main__":
    parse_curriculum()

