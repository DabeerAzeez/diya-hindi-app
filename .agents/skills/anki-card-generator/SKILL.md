---
name: anki-card-generator
description: Generate novel, high-yield Hindi flashcards checked against the student's live Anki deck via AnkiConnect, render an interactive visual HTML card preview widget in chat, and push approved cards to Anki.
---

# Anki Card & Phrase Generator (`/cards`)

Use this skill whenever the user types `/cards`, asks to generate flashcards, or prepares practice phrases for Anki.

## Core Rules & Principles

1. **Complete Sentence Requirement:**
   - Every card **MUST** be a single, complete sentence. Never create isolated words or standalone connectors.
   - Keep foundational cards punchy and concise.

2. **Strict Deck Novelty & Variance Check (Zero-Redundancy Policy):**
   - Query existing cards via [scripts/anki_client.py](./scripts/anki_client.py) or inspect `lessons-dashboard/data/deck_snapshot.json`.
   - **Absolute Uniqueness Requirement:** Proposed cards must NEVER duplicate or near-duplicate existing sentence structures, English prompts, or verb-noun collocations already in the deck.
   - **Lexical & Syntactic Variance:** Actively vary verbs, tenses, subject pronouns, and scenarios. If an existing card uses *"Main coffee pee rahaa hoon"*, do NOT create another coffee card—use a fresh action (e.g., ordering local tea, discussing improv rehearsal, debugging a model, or planning train travel).
   - **Check Algorithm:** Verify that neither the English front nor Hindi target phrase matches any card in `deck_snapshot.json`. If a collision is found, immediately re-roll with an alternate real-world sentence.

3. **Script, Pronunciation & Target Focus Policy:**
   - **NO** Devanagari script anywhere on the Anki cards. Use Romanized Hindi only.
   - Include a second line in gray italics (`#718096`) with macron/dot diacritics for pronunciation guidance.
   - Include a third section in blue (`#2b6cb0`) with word-by-word gloss breakdowns inside `<small>` tags.
   - Include a fourth section in purple (`#6b46c1`) with the explicit **Target Focus** badge:
     e.g., `<small style="color: #6b46c1;"><b>🎯 Target:</b> [A1-07] Shopping & Bargaining (kitne kaa)</small>`. This allows zero-friction failure identification without taking manual notes.

4. **Formality & Speaker Gender Marker:**
   - If subject/gender is not obvious in English, append `(informal, m)`, `(formal, m)`, etc., to the English front text.

5. **Personal Context Integration:**
   - Draw scenarios from [Learner Profile & Strategy.md](../../../Learner%20Profile%20&%20Strategy.md):
     - Shivani catch-up in Norwich, UK (care home lifestyle coordinator, improv comedy memories, getting beers/cocktails together, life in Norwich).
     - Toronto life, music (guitar, piano), AI job transition, gaming with friends.

6. **High-ROI Hinglish Lexicon Priority Rule (Anti-Repetition & Lexicon Audit):**
   - Flashcards **MUST** systematically draw and recycle vocabulary from the **High-ROI B1 Hinglish Lexicon (Core 200 Anchor List)** in [hindi_curriculum_a0_to_a2.md](../../../hindi_curriculum_a0_to_a2.md) (Top 50 Verbs, Top 100 Nouns, Top 50 Adjectives) or `lessons-dashboard/data/high_roi_lexicon.json`.
   - **Mandatory Pre-Generation Dashboard / Lexicon Audit:**
     - Before generating cards, run `python scripts/check_lexicon_coverage.py` or inspect the dashboard's High-ROI Lexicon tab to identify anchors that are **Untargeted (0 cards)** or **Low Coverage (1 card)**.
     - **Lexicon Quota:** Every card generation batch (3 to 5 cards) MUST deliberately incorporate at least **1 to 2 untargeted or low-coverage vocabulary anchors** (e.g., untargeted verbs like *uthaanaa, chalaanaa, khadaa honaa, bhejnaa, le jaanaa, uthnaa, yaad aanaa, maangnaa, sambhaalnaa, bachnaa, girnaa*).
     - Explicitly note which high-ROI anchors are being targeted in the card preview summary (e.g., `📌 High-ROI Anchor: uthaanaa (to pick up)`).
   - **Strict Anti-Repetition Constraints:**
     - Do **NOT** fall back to the same repetitive verbs over and over (*karnaa, bolnaa, dekhnaa, peenaa, aanaa, jaanaa*).
     - Do **NOT** repeat the same scenarios (e.g., another coffee order, another generic office call, another standard beer). While drawing from the learner profile (Shivani in Norwich, music, AI work) is essential, ground those themes in varied, real-life verbs and fresh situations (e.g., picking up bags from Norwich station, handling an improv scheduling mistake, warning someone to watch out/escape the rain, remembering a guitar chord, sending code/files).
   - **The Hinglish Reality Check:**
     - Target the words that native urban speakers *instinctively keep in Hindi* (e.g., *faisla, umeed, bharosa, farq, baat, waqt, rasta, jagah, thanda/garam, ajeeb, zaroori, mushkil, saaf/gandaa, rakhna, chhodna, sambhaalna*).
     - **Strictly AVOID low-ROI formal/Sanskritized words** that bilingual speakers universally say in English (e.g., do *NOT* test *pustak* for book, *kalam* for pen, *aspataal* for hospital, *railgaadi* for train, *pariksha* for exam, *durvaani* for phone, *mitra* for friend).
     - Pair high-ROI Hindi anchors with natural English loan nouns (*pub, meeting, office, coffee, call, flight, project, plan*) to create authentic conversational Hinglish.

---

## Visual Verification & Push Workflow

1. **Draft Cards:** Generate the desired number of cards (typically 3 to 5).
2. **Generate Visual Preview Widget:**
   - Run [scripts/card_preview_generator.py](./scripts/card_preview_generator.py) to generate an interactive HTML preview widget at `preview/card_preview.html`.
   - Embed the preview directly into the chat response using:
     ```html
     <agent-embed src="file:///g:/My Drive/Extracurriculars & Projects/Hindi Coach/preview/card_preview.html"></agent-embed>
     ```
   - Also print the card summary in the chat response for quick reading.
3. **Verification Prompt:**
   - Ask the student: *"Aapko ye cards pasand aaye? If they look good, just say 'Push' and I'll add them straight into your Anki deck!"*
4. **Direct Push Execution:**
   - When the student approves, call:
     ```bash
     python ".agents/skills/anki-card-generator/scripts/anki_client.py" add --front "..." --back "..." --lesson "A1-07"
     ```
   - Confirm added note IDs to the user.

---

## Lessons Dashboard In-App Integration
The Lessons Dashboard provides an in-app "✨ Generate Cards" modal for unlocked lessons.
- When clicked, candidate cards verified against this skill are presented with side-by-side English Front and Hinglish Back previews.
- The student can approve/reject individual cards or click "Approve All".
- Approved cards are added into the Anki queue via `/api/add-cards`, dynamically updating lesson statuses (e.g. converting "Needs Cards" into "Learning").
