"""
High-ROI Lexicon Coverage Checker
Audits the student's Anki deck against the 200 Core High-ROI Anchors
(50 Verbs, 100 Nouns, 50 Adjectives) from the Hindi Curriculum.
"""

import os
import sys
import json
import re
import argparse

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LEXICON_PATH = os.path.join(BASE_DIR, 'lessons-dashboard', 'data', 'high_roi_lexicon.json')
DECK_PATH = os.path.join(BASE_DIR, 'lessons-dashboard', 'data', 'deck_snapshot.json')

def normalize(text):
    t = re.sub(r'<[^>]+>', ' ', text).lower()
    t = re.sub(r'[????]', 'aa', t)
    t = re.sub(r'[????]', 'ee', t)
    t = re.sub(r'[????]', 'oo', t)
    t = re.sub(r'[??]', 'r', t)
    t = re.sub(r'[?]', 'd', t)
    t = re.sub(r'[?]', 't', t)
    t = re.sub(r'[?????]', 'n', t)
    t = re.sub(r'[\'\".,?!/\\:;()\-]', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

VERB_STEM_OVERRIDES = {
    'karnaa': [r'\bkar', r'\bkiy[aie]+', r'\bkijiy'],
    'honaa': [r'\bho', r'\bhuaa?\b', r'\bhui\b', r'\bhue\b', r'\bhotaa?\b', r'\bhoti\b', r'\bhote\b'],
    'jaanaa': [r'\bjaa', r'\bgay[aie]+\b'],
    'aanaa': [r'\baa[ntoyeg]', r'\baay[aie]+\b', r'\baao\b', r'\baaiy'],
    'lenaa': [r'\ble[ntoged]', r'\bliy[aie]+\b', r'\blijiye\b', r'\blee\b'],
    'denaa': [r'\bde[ntoged]', r'\bdiy[aie]+\b', r'\bdijiye\b', r'\bdee\b'],
    'bolnaa': [r'\bbol'],
    'kehnaa': [r'\bkeh', r'\bkah[aie]+'],
    'bataanaa': [r'\bbataa'],
    'baat karnaa': [r'\bbaat\s+kar', r'\bbaat\s+kiy', r'\bbaat\s+karn'],
    'dekhnaa': [r'\bdekh'],
    'sunnaa': [r'\bsun'],
    'samajhnaa': [r'\bsamajh'],
    'sochnaa': [r'\bsoch'],
    'jaannaa': [r'\bjaan'],
    'pataa honaa': [r'\bpataa?\b'],
    'rakhnaa': [r'\brakh'],
    'chhodnaa': [r'\bchhod', r'\bchod'],
    'uthaanaa': [r'\buthaa'],
    'pakadnaa': [r'\bpakad'],
    'pahunchnaa': [r'\bpahunch'],
    'nikalnaa': [r'\bnikal'],
    'ruknaa': [r'\bruk'],
    'roknaa': [r'\brok'],
    'chalnaa': [r'\bchal[ntogeaiy]'],
    'chalaanaa': [r'\bchalaa'],
    'baithnaa': [r'\bbaith'],
    'khadaa honaa': [r'\bkhad[aie]+\s+ho'],
    'milnaa': [r'\bmil'],
    'dhoondhnaa': [r'\bdhoondh', r'\bdhundh'],
    'bhejnaa': [r'\bbhej'],
    'laanaa': [r'\blaa[ntoyeg]', r'\blaay[aie]+\b'],
    'le jaanaa': [r'\ble\s+jaa', r'\ble\s+gay'],
    'khaanaa': [r'\bkhaa[ntoyeg]', r'\bkhaay[aie]+\b'],
    'peenaa': [r'\bpee[ntoyeg]', r'\bpeey[aie]+\b', r'\bpiy[aie]+\b'],
    'sonaa': [r'\bso[ntoyeg]', r'\bsoy[aie]+\b'],
    'uthnaa': [r'\buth[ntogeaiy]'],
    'hansnaa': [r'\bhans', r'\bhas'],
    'ronaa': [r'\bro[ntoyeg]', r'\broy[aie]+\b'],
    'bhoolnaa': [r'\bbhool', r'\bbhul'],
    'yaad aanaa': [r'\byaad\b'],
    'maangnaa': [r'\bmaang'],
    'khelnaa': [r'\bkhel'],
    'bajaanaa': [r'\bbajaa'],
    'seekhnaa': [r'\bseekh', r'\bsikh[ntog]'],
    'sikhaanaa': [r'\bsikhaa'],
    'sambhaalnaa': [r'\bsambhaal'],
    'bachnaa': [r'\bbach'],
    'girnaa': [r'\bgir'],
    'lagnaa': [r'\blag'],
}

def get_word_patterns(word, category):
    raw = word.lower().strip()
    if category == 'verbs' and raw in VERB_STEM_OVERRIDES:
        return VERB_STEM_OVERRIDES[raw]
    
    sub_words = [s.strip() for s in raw.split('/')]
    patterns = []
    for sw in sub_words:
        if ' ' in sw:
            parts = sw.split()
            stem0 = parts[0].rstrip('aeiou')
            stem1 = parts[1].rstrip('aeiou')
            patterns.append(r'\b' + re.escape(stem0) + r'\w*\s+' + re.escape(stem1) + r'\w*')
        else:
            stem = sw.rstrip('aeiou')
            if len(stem) >= 3:
                patterns.append(r'\b' + re.escape(stem) + r'[aieou]*\b')
            else:
                patterns.append(r'\b' + re.escape(sw) + r'\b')
    return patterns

def check_coverage(output_json=False):
    with open(LEXICON_PATH, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)

    with open(DECK_PATH, 'r', encoding='utf-8') as f:
        deck = json.load(f)

    cards = deck['cards'] if isinstance(deck, dict) and 'cards' in deck else deck

    card_entries = []
    for idx, c in enumerate(cards):
        front = c.get('front') or c.get('fields', {}).get('Front', {}).get('value', '')
        back = c.get('back') or c.get('fields', {}).get('Back', {}).get('value', '')
        status = c.get('status', 'Learning')
        card_id = c.get('cardId') or c.get('noteId') or idx
        norm_back = normalize(back)
        card_entries.append({
            'cardId': card_id,
            'front': front,
            'back': back,
            'status': status,
            'norm_back': norm_back
        })

    categories = ['verbs', 'nouns', 'adjectives']
    report = {
        'summary': {},
        'categories': {}
    }

    total_words = 0
    total_targeted = 0

    for cat in categories:
        items = lexicon.get(cat, [])
        cat_total = len(items)
        cat_targeted = 0
        cat_details = []

        for item in items:
            word = item['word']
            patterns = get_word_patterns(word, cat)
            matched_cards = []
            for c in card_entries:
                if any(re.search(p, c['norm_back']) for p in patterns):
                    matched_cards.append({
                        'cardId': c['cardId'],
                        'front': c['front'],
                        'status': c['status']
                    })
            
            cnt = len(matched_cards)
            if cnt > 0:
                cat_targeted += 1
            
            cat_details.append({
                'id': item.get('id'),
                'word': word,
                'diacritics': item.get('diacritics', ''),
                'meaning': item.get('meaning', ''),
                'collocation': item.get('sample') or item.get('collocation', ''),
                'card_count': cnt,
                'matched_cards': matched_cards
            })

        pct = round((cat_targeted / cat_total) * 100) if cat_total else 0
        report['categories'][cat] = {
            'total': cat_total,
            'targeted': cat_targeted,
            'percentage': pct,
            'words': cat_details
        }
        total_words += cat_total
        total_targeted += cat_targeted

    total_pct = round((total_targeted / total_words) * 100) if total_words else 0
    report['summary'] = {
        'total_anchors': total_words,
        'total_targeted': total_targeted,
        'total_untargeted': total_words - total_targeted,
        'overall_percentage': total_pct,
        'cards_audited': len(card_entries)
    }

    print('=' * 60)
    print('  ?? HIGH-ROI VOCABULARY COVERAGE AUDIT')
    print(f'  Audited {len(card_entries)} deck cards against {total_words} curriculum anchors')
    print('=' * 60)
    print(f'Total Coverage:     {total_targeted}/{total_words} ({total_pct}%)')
    for cat in categories:
        c_info = report['categories'][cat]
        print(f"  ? {cat.capitalize():11}: {c_info['targeted']}/{c_info['total']} ({c_info['percentage']}%) targeted")
    print('-' * 60)

    # Show top untargeted verbs, nouns, adjectives
    for cat in categories:
        words = report['categories'][cat]['words']
        untargeted = [w for w in words if w['card_count'] == 0]
        print(f"\n? Top Untargeted {cat.capitalize()} ({len(untargeted)} words with 0 cards):")
        sample = untargeted[:8]
        for w in sample:
            print(f"   - {w['word']} ({w['meaning']}) -> {w['collocation']}")

    if output_json:
        out_path = os.path.join(BASE_DIR, 'lessons-dashboard', 'data', 'lexicon_coverage.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f'\n[Saved full audit report to {out_path}]')

    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', action='store_true', help='Export full audit report to JSON')
    args = parser.parse_args()
    check_coverage(output_json=args.json)
