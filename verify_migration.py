import json

with open('diya/data/deck_snapshot.json', encoding='utf-8') as f:
    snap = json.load(f)

print("Total cards in snapshot:", len(snap['cards']))
print("Stats:", snap['stats'])

pool = {}
primary = {}
for c in snap['cards']:
    p = c.get('primary_lesson') or 'general'
    primary[p] = primary.get(p, 0) + 1
    for code in c.get('lesson_codes', []):
        pool[code] = pool.get(code, 0) + 1

lessons = [
    'A0-01', 'A0-02', 'A0-03', 'A0-04', 'A0-05', 'A0-06', 'A0-07', 'A0-08',
    'A1-01', 'A1-02', 'A1-03', 'A1-04', 'A1-05', 'A1-06', 'A1-07', 'A1-08',
    'A1-09', 'A1-10', 'A2-01', 'A2-02', 'A2-07'
]

print(f"{'Lesson':<10} | {'Study Pool':<12} | {'Primary Grading':<16}")
print("-" * 45)
for l in lessons:
    print(f"{l:<10} | {pool.get(l, 0):<12} | {primary.get(l, 0):<16}")
print(f"{'General':<10} | {len([c for c in snap['cards'] if c.get('is_general')]):<12} | {primary.get('general', 0):<16}")

# Verify no duplicate grading
total_graded = sum(primary.get(l, 0) for l in lessons)
print(f"\nTotal curriculum graded cards: {total_graded} + {primary.get('general', 0)} general = {total_graded + primary.get('general', 0)}")
assert (total_graded + primary.get('general', 0)) == len(snap['cards']), "Card count mismatch!"
print("Verification check PASSED! Zero duplicate grading, 100% card integrity.")
