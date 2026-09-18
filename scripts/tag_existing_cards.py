"""
Tagging and Classification Script for Anki Hindi Deck
Analyzes all cards in the deck, categorizes them into lessons based on the
Highest Lesson (Ceiling) Principle, identifies target focus grammar,
and writes preview to preview/proposed_card_tags.json.
Can run with --dry-run or --apply.
"""

import sys
import os
import re
import json
import argparse

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "anki-card-generator")))
from scripts.anki_client import invoke, get_deck_cards

# Curriculum lessons ordered from lowest prerequisite to highest
LESSON_ORDER = [
    "A0-01", "A0-02", "A0-03", "A0-04", "A0-05", "A0-06", "A0-07", "A0-08",
    "A1-01", "A1-02", "A1-03", "A1-04", "A1-05", "A1-06", "A1-07", "A1-08",
    "A1-09", "A1-10", "A2-01", "A2-02", "A2-03", "A2-04", "A2-05", "A2-06",
    "A2-07", "A2-08", "A2-09", "A2-10", "A2-11"
]

LESSON_RANK = {code: idx for idx, code in enumerate(LESSON_ORDER)}

# Reached lessons in study journey
REACHED_LESSONS = set([
    "A0-00", "A0-01", "A0-02", "A0-03", "A0-04",
    "A0-05", "A0-06", "A0-07", "A0-08",
    "A1-01", "A1-02", "A1-03", "A1-04", "A1-05", "A1-06", "A1-07",
    "A1-08", "A1-09"
])

def clean_html(text):
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def extract_hindi_sentence(back_html):
    parts = re.split(r'<br\s*/?>|<span', back_html, flags=re.IGNORECASE)
    first_part = clean_html(parts[0])
    return first_part

def normalize_transliteration(text):
    """Normalize accents, macrons and retroflex diacritics for consistent regex matching."""
    t = text.lower()
    t = re.sub(r'[āàâä]', 'aa', t)
    t = re.sub(r'[īíîï]', 'ee', t)
    t = re.sub(r'[ūúûü]', 'oo', t)
    t = re.sub(r'[ṛř]', 'r', t)
    t = re.sub(r'[ḍ]', 'd', t)
    t = re.sub(r'[ṭ]', 't', t)
    t = re.sub(r'[ṅñṇṁṃ]', 'n', t)
    return t

def classify_card(front, back):
    """
    Evaluates all grammatical concepts present in the sentence,
    and returns (ceiling_lesson, all_matched_lessons, target_focus_description).
    """
    hindi_orig = extract_hindi_sentence(back)
    hindi = normalize_transliteration(hindi_orig)
    front_clean = clean_html(front).lower()

    detected = {}  # lesson_code -> target_focus

    # A2-02: Agentive / Aspectual marker -vaalaa / -waalaa
    if re.search(r'\b\w*(waal[aie]+|wal[aie]+)\b', hindi):
        detected["A2-02"] = "Agentive/Aspectual marker -vaalaa ('about to' / 'the one that is')"

    # A1-09: Conversational Connectors, Discourse Markers & Improv Fillers
    if re.search(r'\b(matlab|yaani|sach mein|arre yaar|sahi baat hai|uske baad|aakhiri mein|iske alaavaa|varna)\b', hindi):
        detected["A1-09"] = "Conversational Connectors, Discourse Markers & Improv Fillers"
    if "pehle" in hindi and ("phir" in hindi or "baad" in hindi):
        detected["A1-09"] = "Chronological sequencers (pehle -> phir / uske baad)"

    # A1-08: Transitive Verbs & Ergative Case Marker (Ne)
    if re.search(r'\b(maine|aapne|usne|unhone|humne|tumne|dost ne|shivani ne)\b', hindi) or re.search(r'\b\w+\s+ne\b', hindi):
        detected["A1-08"] = "Transitive Verbs & Ergative Case Marker (Ne)"

    # A1-10: Clock time & routines
    if re.search(r'\b(baje|kitne baje|savaa|saadhe|paune)\b', hindi) or "what time" in front_clean or "o'clock" in front_clean:
        detected["A1-10"] = "Clock time & routine numbers (baje, saadhe, etc.)"


    # A1-07: Shopping, quantifiers, bargaining
    if re.search(r'\b(kitn[aie]+ kaa?|kitn[aie]+ kee?|kitn[aie]+ ke|kitn[aie]+ huaa?|rupay[aie]+|mehe?ng[aie]+|sast[aie]+|thod[aie]+ kam|kam karo|zyaadaa?|zyadaa?)\b', hindi) or "how much" in front_clean or "bargain" in front_clean or "expensive" in front_clean or "cost" in front_clean:
        detected["A1-07"] = "Shopping, bargaining & quantifiers (kitne kaa, mehenga, sasta)"

    # A1-06: Communication verbs
    if re.search(r'\b(bataai?y[aie]+|bataao|bataan[aie]+|kehn[aie]+|kahaa?|baat karn[aie]+|baat kar[aie]+|baat kar|boln[aie]+|bolt[aie]+)\b', hindi):
        detected["A1-06"] = "Communication verbs (bolna, kehna, bataana, baat karna)"

    # A1-05: Habitual past / past continuous (taa thaa, rahaa thaa)
    if re.search(r'\b(t[aie]+ th[aie]+|rah[aie]+ th[aie]+)\b', hindi) or "used to" in front_clean or "was doing" in front_clean:
        detected["A1-05"] = "Habitual past or past continuous (taa thaa / rahaa thaa)"

    # A1-04: Obligation & compulsion (padtaa hai, karna hai, nikalna hai)
    if re.search(r'\b(padt[aie]+|padeg[aie]+)\s+(hai|hain|ho|thaa|thee)?\b', hindi) or re.search(r'\b\w+n[aie]+\s+hai\b', hindi):
        if not re.search(r'\bmanaa\s+hai\b', hindi):
            detected["A1-04"] = "Obligation & compulsion (padtaa hai / infinitive+hai)"

    # A1-03: Subordinating conjunction 'ki'
    if re.search(r'\b(soch[aie]+ ki|lagt[aie]+ ki|pataa? ki|kahaa? ki|jaant[aie]+ ki|bol[aie]+ ki)\b', hindi) or (re.search(r'\bki\b', hindi) and ("that" in front_clean or "know" in front_clean)):
        detected["A1-03"] = "Subordinating conjunction 'ki' (linking clauses)"

    # A1-02: Possessives & Relationships (meraa, aapkaa, dost, pati, umar, etc.)
    if re.search(r'\b(mer[aie]+|aapk[aie]+|isk[aie]+|usk[aie]+|tumhaar[aie]+|tumhar[aie]+|humaar[aie]+|humar[aie]+|unk[aie]+|bhaai|behen|dost|family|umar|pati|patni|ki job|ki train|ki keys)\b', hindi):
        if not re.search(r'\b(mere|tumhare|tumhaare|aapke|humaare|humare|uske|unke) paas\b', hindi):
            detected["A1-02"] = "Possessive pronouns & relationships (meraa, aapkaa, etc.)"
    if "acoustic guitar" in hindi and ("aapki" in hindi or "aapkee" in hindi):
        detected["A1-02"] = "Possessive pronoun agreement (aapki guitar)"
    if "ye billi meri hai" in hindi:
        detected["A1-02"] = "Possessive pronouns (mine, yours, his, ours)"

    # A1-01: Imperatives & Giving directions (kijiye, karo, aaiye, aao, rukiye, baithiye, seedha, daayein, baayein, aage, peeche)
    if re.search(r'\b(kijiy[aie]+|karo|aaiy[aie]+|aao|jaaiy[aie]+|jaao|dekhiy[aie]+|dekho|suniy[aie]+|suno|rukiy[aie]+|ruko|baithiy[aie]+|rakho|mudiy[aie]+|chalo|mat)\b', hindi) or (re.search(r'\b(seedh[aie]+|daayein|baayein|aage|peeche|kidhar|idhar|udhar)\b', hindi) and ("turn" in front_clean or "straight" in front_clean or "ahead" in front_clean or "behind" in front_clean or "where" in front_clean)):
        detected["A1-01"] = "Imperatives & Giving directions (kijiye/karo/mat/directions)"
    if re.search(r'\bmanaa\s+hai\b', hindi):
        detected["A1-01"] = "Prohibitive instruction (manaa hai - forbidden)"

    # A0-08: Simple future tense (-ūngaa, -enge, -oge, -egaa)
    if re.search(r'\b(\w+oo[n]?g[aie]+|\w+aa?yeg[aie]+|\w+aa?yenge|\w+enge|\w+oge|\w+eg[aie]+|hog[aie]+)\b', hindi) and not re.search(r'\b(karo|aao|jaao|dekho|suno|ruko|rakho)\b', hindi):
        detected["A0-08"] = "Simple future tense (-ūngaa, -enge, -egaa)"

    # A0-06: Simple past tense & completed actions (gaya, aaya, kiya, bola, thaa, etc.)
    if re.search(r'\b(gay[aie]+|aay[aie]+|kiy[aie]+|bol[aie]+|mili|samajh gay[aie]+|padh[aie]+|bhool gay[aie]+|ho gay[aie]+)\b', hindi) or (re.search(r'\b(th[aie]+)\b', hindi) and not re.search(r'\b(t[aie]+|rah[aie]+|sakt[aie]+|chahiye)\b', hindi)):
        detected["A0-06"] = "Simple past tense & completed actions (gayaa, thaa, kiyaa)"

    # A0-05: Oblique shift (infinitive + postposition: -ne ke liye, -ne se pehle, -ne ke baad)
    if re.search(r'\w+ne\s+(ke liye|se pehle|ke baad|par|se|ko|kaa|kee|ke)\b', hindi) or re.search(r'\b(apne|kamre mein?|raste par)\b', hindi):
        detected["A0-05"] = "The Oblique Shift (infinitive + postposition: -ne ke liye / baad)"

    # A0-04: Can and Want (saktaa, chaahtaa, chaahiye, pasand, zaroorat)
    if re.search(r'\b(sakt[aie]+|chaa?ht[aie]+|chaa?hiye|pasand|zaroorat)\b', hindi):
        detected["A0-04"] = "Can & Want (saktaa, chaahtaa, chaahiye, pasand)"

    # A0-03: Relational postpositions & connectors (ke saath, ke paas, ke baare me, ke liye, isliye, kyunki, lekin, vaise)
    if re.search(r'\b(ke saath|ke paas|ke baare|isliye|kyunki|lekin|vaise)\b', hindi) or re.search(r'\bke liye\b', hindi) or re.search(r'\b(mere|tumhare|tumhaare|aapke|humaare|humare|uske|unke) paas\b', hindi):
        detected["A0-03"] = "Relational postpositions & connectors (ke saath, ke paas, ke liye, isliye)"

    # A0-02: Present Continuous & Present Habitual (rahaa hoon, taa hoon)
    if re.search(r'\b(rah[aie]+)\s+(hoon|hai|hain|ho)\b', hindi) or re.search(r'\b(t[aie]+)\s+(hoon|hai|hain|ho)\b', hindi) or re.search(r'\b(kart[aie]+|raht[aie]+|samajht[aie]+|khelt[aie]+|jaat[aie]+|hote|lete|seekh|sunt[aie]+)\s+(hoon|hai|hain|ho)\b', hindi):
        detected["A0-02"] = "Present Continuous (-rahaa hoon) or Present Habitual (-taa hoon)"

    # A0-01: Foundational 'To Be', Pronouns, Greetings
    if re.search(r'\b(namaste|kaise hain|kaisen? ho|kaisee? hain|kaisee? ho|theek|amriki|angrez|alvida|shukriya)\b', hindi):
        detected["A0-01"] = "Foundational greetings, pronouns & 'To Be' verbs"
    if re.search(r'\b(hoon|hai|hain|ho)\b', hindi):
        detected["A0-01"] = "Foundational 'To Be' verb (hoon/hai/ho/hain)"

    valid_codes = [code for code in detected if code in LESSON_RANK]
    if not valid_codes:
        return "general", ["general"], "General conversational phrase or idiom"

    # Ceiling is the highest-ranking lesson
    ceiling_code = max(valid_codes, key=lambda c: LESSON_RANK[c])
    return ceiling_code, valid_codes, detected[ceiling_code]

def determine_tags(ceiling_code):
    if ceiling_code == "general":
        return ["lesson::general"]
    elif ceiling_code in REACHED_LESSONS:
        return [f"lesson::{ceiling_code}"]
    else:
        # Sneak-peek future lesson: dual tag
        return ["lesson::general", f"lesson::{ceiling_code}"]

def process_deck(dry_run=True):
    cards = get_deck_cards("Hindi")
    print(f"Auditing {len(cards)} cards from deck 'Hindi' using the Ceiling Principle...")

    tagged_data = []
    lesson_counts = {}
    general_count = 0
    sneak_peek_count = 0

    for c in cards:
        front = c["fields"]["Front"]["value"]
        back = c["fields"]["Back"]["value"]
        note_id = c["note"]
        card_id = c["cardId"]

        ceiling_code, all_matched, target_focus = classify_card(front, back)
        tags = determine_tags(ceiling_code)

        if "lesson::general" in tags and len(tags) > 1:
            sneak_peek_count += 1
        elif "lesson::general" in tags:
            general_count += 1
        else:
            lesson_counts[ceiling_code] = lesson_counts.get(ceiling_code, 0) + 1

        tagged_data.append({
            "cardId": card_id,
            "noteId": note_id,
            "front": clean_html(front),
            "hindi": extract_hindi_sentence(back),
            "lesson": ceiling_code,
            "all_matched": all_matched,
            "target_focus": target_focus,
            "tags": tags,
            "interval": c.get("interval", 0),
            "reps": c.get("reps", 0),
            "lapses": c.get("lapses", 0),
            "queue": c.get("queue", 0),
            "factor": c.get("factor", 2500)
        })

    print("\n--- REFINED CEILING CLASSIFICATION SUMMARY ---")
    for code in LESSON_ORDER:
        if code in lesson_counts:
            print(f"  {code}: {lesson_counts[code]} cards")
    print(f"  General (Pure): {general_count} cards")
    print(f"  Sneak-Peeks (Future Lessons): {sneak_peek_count} cards")
    print(f"  Total Processed: {len(tagged_data)} cards")

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "preview"))
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "proposed_card_tags.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(tagged_data, f, indent=2, ensure_ascii=False)
    print(f"\nProposed tag mapping saved to: {out_file}")

    if not dry_run:
        print("\nApplying updated tags to Anki via AnkiConnect...")
        for item in tagged_data:
            note_id = item["noteId"]
            current_tags = item.get("tags", [])
            tag_str = " ".join(current_tags)
            invoke("addTags", notes=[note_id], tags=tag_str)
        print("Successfully applied updated ceiling tags to all notes in Anki!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tag existing cards in Anki Hindi deck using Ceiling Principle")
    parser.add_argument("--apply", action="store_true", help="Apply tags to Anki (defaults to dry-run preview)")
    args = parser.parse_args()

    process_deck(dry_run=not args.apply)
