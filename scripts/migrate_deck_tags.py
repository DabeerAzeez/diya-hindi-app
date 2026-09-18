#!/usr/bin/env python3
"""
Migrate Anki Deck Tags to Multi-Tag System with Highest-Prerequisite Grading Rule.
- Backs up all current note tags to a timestamped JSON file.
- Replaces legacy/erroneous tags with linguistic multi-tags.
- Cleans untagged general cards (idioms, songs, test cards).
- Refreshes diya/data/deck_snapshot.json with highest-prerequisite primary_lesson resolution.
"""

import urllib.request
import urllib.error
import json
import os
import sys
import time
import argparse

ANKI_URL = 'http://127.0.0.1:8765'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DATA_DIR = os.path.join(PROJECT_DIR, 'diya', 'data')
SNAPSHOT_FILE = os.path.join(DATA_DIR, 'deck_snapshot.json')
MAP_FILE = r'C:\Users\dabee\.gemini\antigravity\brain\e457b3a1-0d60-4907-af67-6cffcf51e50c\scratch\clean_multi_tags.json'

LESSON_HIERARCHY = [
    'A0-X', 'A0-01', 'A0-02', 'A0-03', 'A0-04', 'A0-05', 'A0-06', 'A0-07', 'A0-08',
    'A1-01', 'A1-02', 'A1-03', 'A1-04', 'A1-05', 'A1-06', 'A1-07', 'A1-08', 'A1-09', 'A1-10',
    'A2-01', 'A2-02', 'A2-03', 'A2-04', 'A2-05', 'A2-06', 'A2-07', 'A2-08',
    'B1-01', 'B1-02', 'B1-03', 'B1-04', 'B1-05'
]

def anki_request(action, params=None):
    payload = json.dumps({'action': action, 'params': params or {}, 'version': 6}).encode('utf-8')
    req = urllib.request.Request(ANKI_URL, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('error'):
                raise Exception(data['error'])
            return data.get('result')
    except Exception as e:
        print(f"Error calling AnkiConnect action '{action}': {e}", file=sys.stderr)
        raise

def main():
    parser = argparse.ArgumentParser(description="Migrate Anki Deck Tags")
    parser.add_argument('--dry-run', action='store_true', help="Simulate migration without modifying Anki")
    args = parser.parse_args()

    print("=" * 65)
    print("  Anki Deck Multi-Tag Migration (Highest-Prerequisite Rule)")
    print("=" * 65)

    if not os.path.exists(MAP_FILE):
        print(f"Error: Multi-tag mapping file not found at {MAP_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        clean_records = json.load(f)

    target_map = {r['noteId']: r for r in clean_records}
    print(f"Loaded target mapping for {len(target_map)} notes.")

    # 1. Connect to Anki
    try:
        version = anki_request('version')
        print(f"Connected to AnkiConnect (API version {version}).")
    except Exception as e:
        print(f"Failed to connect to AnkiConnect at {ANKI_URL}. Is Anki running?", file=sys.stderr)
        sys.exit(1)

    # 2. Fetch all notes in 'Hindi' deck
    note_ids = anki_request('findNotes', {'query': 'deck:Hindi'})
    print(f"Found {len(note_ids)} notes in deck 'Hindi'.")

    notes_info = anki_request('notesInfo', {'notes': note_ids})

    # 3. Create timestamped safety backup
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(DATA_DIR, f'anki_tags_backup_{timestamp}.json')
    backup_data = [{'noteId': n['noteId'], 'tags': n.get('tags', [])} for n in notes_info]
    
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    print(f"Safety backup created at: {backup_path} ({len(backup_data)} notes saved).")

    if args.dry_run:
        print("\n[DRY RUN] Simulating tag updates...")
        for n in notes_info[:10]:
            nid = n['noteId']
            old_tags = n.get('tags', [])
            rec = target_map.get(nid)
            new_tags = rec['tags'] if rec else []
            print(f"Note {nid}: {old_tags} --> {new_tags} (Primary: {rec.get('primary_lesson') if rec else 'None'})")
        print("\nDry run completed successfully. No changes were written to Anki.")
        return

    # 4. Execute tag updates in Anki
    print("\nUpdating tags in Anki...")
    updated_count = 0
    cleared_count = 0

    for idx, n in enumerate(notes_info, 1):
        nid = n['noteId']
        old_tags = n.get('tags', [])
        rec = target_map.get(nid)

        if not rec:
            continue

        target_tags = set(rec['tags'])
        current_set = set(old_tags)

        # Tags to remove: any lesson::*, lesson_*, hindi-coach, hindi_coach tags not in target_tags
        tags_to_remove = [
            t for t in old_tags
            if (t.startswith('lesson::') or t.startswith('lesson_') or t in ['hindi-coach', 'hindi_coach'])
            and t not in target_tags
        ]

        # Tags to add: target_tags not currently on note
        tags_to_add = [t for t in target_tags if t not in current_set]

        if tags_to_remove:
            anki_request('removeTags', {'notes': [nid], 'tags': ' '.join(tags_to_remove)})

        if tags_to_add:
            anki_request('addTags', {'notes': [nid], 'tags': ' '.join(tags_to_add)})

        if tags_to_remove or tags_to_add:
            updated_count += 1
            if not target_tags:
                cleared_count += 1

        if idx % 50 == 0 or idx == len(notes_info):
            print(f"  Processed {idx}/{len(notes_info)} notes...")

    print(f"\nTags successfully updated for {updated_count} notes ({cleared_count} untagged as general).")

    # 5. Refresh deck_snapshot.json with highest prerequisite logic
    print("Refreshing DIYA deck snapshot with highest-prerequisite primary lessons...")
    refreshed_cards_info = anki_request('cardsInfo', {'cards': anki_request('findCards', {'query': 'deck:Hindi'})})
    notes_map = {}
    for n in anki_request('notesInfo', {'notes': note_ids}):
        notes_map[n['noteId']] = n.get('tags', [])

    processed_cards = []
    mastered_count = 0
    learning_count = 0
    struggling_count = 0

    for c in refreshed_cards_info:
        cid = c.get('cardId')
        nid = c.get('note')
        interval = c.get('interval', 0)
        reps = c.get('reps', 0)
        lapses = c.get('lapses', 0)
        queue = c.get('queue', 0)
        factor = c.get('factor', 2500)
        tags = notes_map.get(nid, [])

        if queue == 0 or reps == 0:
            status = 'Learning'
            learning_count += 1
        elif queue == 1 or (lapses >= 2 and interval < 7) or (factor < 1700 and interval < 7):
            status = 'Struggling'
            struggling_count += 1
        elif interval >= 14 and reps >= 3:
            status = 'Mastered'
            mastered_count += 1
        else:
            status = 'Learning'
            learning_count += 1

        lesson_codes = []
        is_general = False
        for t in tags:
            if t.startswith('lesson::'):
                code = t[len('lesson::'):].strip()
                if code.lower() == 'general':
                    is_general = True
                elif code:
                    lesson_codes.append(code)

        sorted_codes = sorted(
            lesson_codes,
            key=lambda x: LESSON_HIERARCHY.index(x) if x in LESSON_HIERARCHY else -1
        )
        primary_lesson = sorted_codes[-1] if sorted_codes else ('general' if is_general else '')

        fields = c.get('fields', {})
        front_val = fields.get('Front', {}).get('value', '') or fields.get('Text', {}).get('value', '')
        back_val = fields.get('Back', {}).get('value', '')

        processed_cards.append({
            'cardId': cid,
            'noteId': nid,
            'front': front_val or c.get('question', ''),
            'back': back_val or c.get('answer', ''),
            'interval': interval,
            'reps': reps,
            'lapses': lapses,
            'queue': queue,
            'factor': factor,
            'status': status,
            'tags': tags,
            'lesson_codes': sorted_codes,
            'primary_lesson': primary_lesson,
            'is_general': is_general
        })

    snapshot_data = {
        'synced_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'stats': {
            'total': len(processed_cards),
            'Mastered': mastered_count,
            'Learning': learning_count,
            'Struggling': struggling_count
        },
        'cards': processed_cards
    }

    with open(SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

    print(f"Saved refreshed snapshot to {SNAPSHOT_FILE} ({len(processed_cards)} cards).")
    print("\nMigration completed successfully!")

if __name__ == '__main__':
    main()
