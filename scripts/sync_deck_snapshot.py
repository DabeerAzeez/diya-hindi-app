"""
Sync Deck Snapshot for lessons-dashboard
Fetches all cards and tags from Anki via AnkiConnect, computes card health status
using the Ceiling Principle and Target Focus, and writes to lessons-dashboard/data/deck_snapshot.json.
"""

import os
import sys
import json
import datetime

sys.stdout.reconfigure(encoding='utf-8')
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "scripts"))
sys.path.append(os.path.join(root_dir, ".agents", "skills", "anki-card-generator", "scripts"))
from anki_client import get_deck_cards
from tag_existing_cards import classify_card, clean_html

def evaluate_card_status(interval, reps, lapses, queue, factor):
    """
    Card health evaluation (Recovery-Aware):
    - Unreviewed / Brand New: queue == 0 or reps == 0 -> Learning (never Struggling)
    - Struggling (Red): Active lapse or leech in short interval:
        queue == 1 (in relearning) OR
        (lapses >= 2 and interval < 7) OR
        (factor < 1700 and interval < 7)
    - Mastered (Green): interval >= 14 and reps >= 3 (proves long-term retention, regardless of past lapses)
    - Learning (Yellow): otherwise (interval 1..13, recovering cards with interval 7..13, or new cards)
    """
    # Brand new / unreviewed cards are in Learning, NEVER Struggling!
    if queue == 0 or reps == 0:
        return "Learning"
    # Active struggling: currently in relearning or multiple lapses with short interval (< 7 days)
    if queue == 1 or (lapses >= 2 and interval < 7) or (factor < 1700 and interval < 7):
        return "Struggling"
    # Mastered: card has demonstrated robust retention across weeks
    if interval >= 14 and reps >= 3:
        return "Mastered"
    return "Learning"

def sync_snapshot():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(base_dir, "lessons-dashboard", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "deck_snapshot.json")

    print("Querying AnkiConnect for Hindi deck cards...")
    cards = get_deck_cards("Hindi", include_tags=True)
    print(f"Retrieved {len(cards)} cards.")

    processed_cards = []
    stats = {
        "total": len(cards),
        "Mastered": 0,
        "Learning": 0,
        "Struggling": 0
    }

    for c in cards:
        interval = c.get("interval", 0)
        reps = c.get("reps", 0)
        lapses = c.get("lapses", 0)
        queue = c.get("queue", 0)
        factor = c.get("factor", 2500)
        tags = c.get("tags", [])
        front = c["fields"]["Front"]["value"]
        back = c["fields"]["Back"]["value"]

        status = evaluate_card_status(interval, reps, lapses, queue, factor)
        stats[status] += 1

        # Check explicit lesson tags first from Anki
        explicit_lesson = None
        for t in tags:
            if t.startswith("lesson::") and t != "lesson::general":
                explicit_lesson = t.split("::", 1)[1]
                break

        ceiling_code, all_matched, target_focus = classify_card(front, back)

        # If explicit lesson tag is present on card, prioritize it as primary ceiling
        primary_code = explicit_lesson if explicit_lesson else ceiling_code
        is_general = (primary_code == "general")
        lesson_codes = [primary_code] if not is_general else []

        # Keep any secondary or matched tags present
        for t in tags:
            if t.startswith("lesson::"):
                code = t.split("::", 1)[1]
                if code != "general" and code not in lesson_codes:
                    lesson_codes.append(code)

        processed_cards.append({
            "cardId": c["cardId"],
            "noteId": c["note"],
            "front": front,
            "back": back,
            "interval": interval,
            "reps": reps,
            "lapses": lapses,
            "queue": queue,
            "factor": factor,
            "status": status,
            "tags": tags,
            "primary_lesson": primary_code,
            "target_focus": target_focus,
            "all_matched_lessons": all_matched,
            "lesson_codes": lesson_codes,
            "is_general": is_general
        })

    snapshot_data = {
        "synced_at": datetime.datetime.now().isoformat(),
        "stats": stats,
        "cards": processed_cards
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

    js_file = os.path.join(out_dir, "snapshot_data.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write("window.DECK_SNAPSHOT = " + json.dumps(snapshot_data, indent=2, ensure_ascii=False) + ";\n")

    print(f"Successfully wrote deck snapshot to {out_file} and {js_file}!")
    print(f"Stats: Mastered={stats['Mastered']} | Learning={stats['Learning']} | Struggling={stats['Struggling']}")

if __name__ == "__main__":
    sync_snapshot()
