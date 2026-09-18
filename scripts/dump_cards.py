import sys
import json
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "anki-card-generator")))
from scripts.anki_client import get_deck_cards

def main():
    cards = get_deck_cards("Hindi")
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "preview"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "all_cards_dump.json")
    
    clean_cards = []
    for c in cards:
        clean_cards.append({
            "id": c["cardId"],
            "note": c["note"],
            "front": c["fields"]["Front"]["value"],
            "back": c["fields"]["Back"]["value"],
            "interval": c["interval"],
            "reps": c["reps"],
            "lapses": c["lapses"],
            "queue": c["queue"],
            "factor": c["factor"],
            "tags": c.get("tags", [])
        })
        
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clean_cards, f, indent=2, ensure_ascii=False)
        
    print(f"Dumped {len(clean_cards)} cards to {out_path}")

if __name__ == "__main__":
    main()
