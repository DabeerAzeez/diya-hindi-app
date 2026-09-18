"""
AnkiConnect Client for Hindi Coach
Interacts with local Anki desktop application via AnkiConnect HTTP API (http://127.0.0.1:8765).
"""

import sys
import json
import urllib.request
import argparse

sys.stdout.reconfigure(encoding='utf-8')

ANKI_URL = "http://127.0.0.1:8765"
DEFAULT_DECK = "Hindi"
DEFAULT_MODEL = "Basic"

def invoke(action, **params):
    payload = json.dumps({"action": action, "params": params, "version": 6}).encode("utf-8")
    req = urllib.request.Request(ANKI_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode("utf-8"))
            if res.get("error"):
                raise RuntimeError(f"AnkiConnect Error: {res['error']}")
            return res.get("result")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not connect to Anki at {ANKI_URL}. Make sure Anki is open with AnkiConnect installed. Error: {e}")

def get_deck_cards(deck_name=DEFAULT_DECK, include_tags=True):
    """Retrieve all cards currently in the specified deck, optionally attaching note tags."""
    card_ids = invoke("findCards", query=f'deck:"{deck_name}"')
    if not card_ids:
        return []
    # Fetch in chunks of 50
    cards = []
    chunk_size = 50
    for i in range(0, len(card_ids), chunk_size):
        chunk = card_ids[i:i + chunk_size]
        cards.extend(invoke("cardsInfo", cards=chunk))
    
    if include_tags and cards:
        note_ids = list({c["note"] for c in cards})
        notes_map = {}
        for i in range(0, len(note_ids), chunk_size):
            n_chunk = note_ids[i:i + chunk_size]
            n_infos = invoke("notesInfo", notes=n_chunk)
            for ni in n_infos:
                notes_map[ni["noteId"]] = ni.get("tags", [])
        for c in cards:
            c["tags"] = notes_map.get(c["note"], [])

    return cards

def add_card(front, back, deck_name=DEFAULT_DECK, tags=None, lesson=None):
    """Add a new basic card to the deck with optional lesson tag."""
    if tags is None:
        tags = ["hindi-coach"]
    elif isinstance(tags, str):
        tags = [tags]
    if lesson:
        lesson_tag = f"lesson::{lesson}" if not lesson.startswith("lesson::") else lesson
        if lesson_tag not in tags:
            tags.append(lesson_tag)
    note = {
        "deckName": deck_name,
        "modelName": DEFAULT_MODEL,
        "fields": {
            "Front": front,
            "Back": back
        },
        "options": {
            "allowDuplicate": False,
            "duplicateScope": "deck"
        },
        "tags": tags
    }
    return invoke("addNote", note=note)

def check_card_novelty(front_text, back_text, existing_cards):
    """Check if front or back text already has close matches in the deck."""
    clean_front = front_text.lower().strip()
    clean_back = back_text.lower().strip()
    matches = []
    for c in existing_cards:
        fields = c.get("fields", {})
        c_front = fields.get("Front", {}).get("value", "").lower()
        c_back = fields.get("Back", {}).get("value", "").lower()
        if clean_front in c_front or c_front in clean_front:
            matches.append(("Front match", fields.get("Front", {}).get("value", "")))
        elif clean_back in c_back or c_back in clean_back:
            matches.append(("Back match", fields.get("Back", {}).get("value", "")))
    return matches

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AnkiConnect CLI for Hindi Coach")
    subparsers = parser.add_subparsers(dest="command")

    # List command
    list_p = subparsers.add_parser("list")
    list_p.add_argument("--deck", default=DEFAULT_DECK)

    # Add command
    add_p = subparsers.add_parser("add")
    add_p.add_argument("--front", required=True)
    add_p.add_argument("--back", required=True)
    add_p.add_argument("--deck", default=DEFAULT_DECK)
    add_p.add_argument("--tags", nargs="*", default=["hindi-coach"])
    add_p.add_argument("--lesson", default=None, help="Curriculum lesson code, e.g. A1-07")

    args = parser.parse_args()

    if args.command == "list":
        cards = get_deck_cards(args.deck)
        print(f"Deck '{args.deck}' has {len(cards)} cards.")
    elif args.command == "add":
        note_id = add_card(args.front, args.back, deck_name=args.deck, tags=args.tags, lesson=args.lesson)
        print(f"Successfully added note {note_id} to deck '{args.deck}'!")
    else:
        parser.print_help()
