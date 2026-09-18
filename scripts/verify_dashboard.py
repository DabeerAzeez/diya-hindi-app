"""
Verification script for Lessons Dashboard data and progression engine
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test_dashboard():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lessons-dashboard", "data"))
    curr_path = os.path.join(base, "curriculum.json")
    deck_path = os.path.join(base, "deck_snapshot.json")

    assert os.path.exists(curr_path), "curriculum.json missing"
    assert os.path.exists(deck_path), "deck_snapshot.json missing"

    with open(curr_path, "r", encoding="utf-8") as f:
        curriculum = json.load(f)

    with open(deck_path, "r", encoding="utf-8") as f:
        deck = json.load(f)

    print(f"Total Curriculum Lessons: {len(curriculum)}")
    print(f"Total Deck Cards: {len(deck['cards'])}")
    print(f"Deck Stats: {deck['stats']}")

    # Simulate Progression & Notion Cap Engine
    cards = deck["cards"]
    lesson_map = {l["code"]: [] for l in curriculum}
    
    for c in cards:
        primary = c.get("primary_lesson") or (c.get("lesson_codes") and c.get("lesson_codes")[0])
        if primary and primary in lesson_map and not c.get("is_general") and primary != "general":
            lesson_map[primary].append(c)

    # Notion Cap Logic: Unlocked strictly if is_completed (or A0-X)
    unlocked_codes = set()
    lesson_statuses = {}
    struggling_active_count = 0

    MIN_CARDS = 5
    MAX_STRUGGLING_ALLOWED = 2

    for l in curriculum:
        code = l["code"]
        if code == "A0-X":
            unlocked_codes.add(code)
            lesson_statuses[code] = "Reference"
            continue

        if l.get("is_completed"):
            unlocked_codes.add(code)
            l_cards = lesson_map[code]
            count = len(l_cards)
            if count < MIN_CARDS:
                status = "Needs Cards"
            else:
                m = sum(1 for c in l_cards if c["status"] == "Mastered")
                s = sum(1 for c in l_cards if c["status"] == "Struggling")
                m_rate = m / count
                s_rate = s / count
                if s_rate >= 0.25 and s >= 2:
                    status = "Struggling"
                    struggling_active_count += 1
                elif m_rate >= 0.65 and s_rate <= 0.20:
                    status = "Mastered"
                else:
                    status = "Learning"
            lesson_statuses[code] = status
        else:
            lesson_statuses[code] = "Locked"

    # General & Sneak-Peek Cards
    general_and_sneak_peeks = [
        c for c in cards
        if not c.get("primary_lesson") or c.get("primary_lesson") == "general" or c.get("is_general") or c.get("primary_lesson") not in unlocked_codes
    ]
    active_cards = [c for c in cards if c not in general_and_sneak_peeks]

    print("\n--- NOTION CAP & LESSON STATUSES ---")
    for l in curriculum:
        code = l["code"]
        status = lesson_statuses[code]
        card_cnt = len(lesson_map[code])
        if status != "Locked":
            print(f"  {code}: {status} ({card_cnt} cards)")
        elif card_cnt > 0:
            print(f"  {code}: 🔒 Locked ({card_cnt} preview cards)")

    # Assertions
    assert "A1-06" in unlocked_codes, "A1-06 must be unlocked"
    assert "A1-07" not in unlocked_codes, "A1-07 must be locked (no Notion page)"
    assert lesson_statuses["A1-07"] == "Locked", "A1-07 status must be Locked"
    assert all(lesson_statuses[l["code"]] == "Locked" for l in curriculum if not l.get("is_completed") and l["code"] != "A0-X"), "All incomplete Notion lessons must be Locked"

    assert len(active_cards) == 137, f"Expected 137 active cards, got {len(active_cards)}"
    assert len(general_and_sneak_peeks) == 45, f"Expected 45 sneak peek / general cards, got {len(general_and_sneak_peeks)}"
    assert len(active_cards) + len(general_and_sneak_peeks) == len(cards), "Card conservation failed"

    # Find next locked lesson for banner
    next_locked = next(l for l in curriculum if lesson_statuses[l["code"]] == "Locked")
    assert next_locked["code"] == "A1-07", f"Expected next locked to be A1-07, got {next_locked['code']}"

    is_ready_for_next = struggling_active_count <= MAX_STRUGGLING_ALLOWED
    print(f"\n--- PROGRESSION ADVISORY FOR {next_locked['code']} ---")
    print(f"  Next Lesson: {next_locked['code']} ({next_locked['title']})")
    print(f"  Active Struggling Lessons: {struggling_active_count} (Limit: {MAX_STRUGGLING_ALLOWED})")
    print(f"  Readiness Status: {'🚀 Ready to Advance (Advisory)' if is_ready_for_next else '⚠️ Review Recommended'}")
    assert is_ready_for_next, "Expected user to be within ready advisory threshold"

    print("\nAll data and Notion Cap assertions passed successfully!")

if __name__ == "__main__":
    test_dashboard()
