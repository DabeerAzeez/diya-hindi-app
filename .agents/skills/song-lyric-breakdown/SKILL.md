---
name: song-lyric-breakdown
description: Deconstruct Hindi and Bollywood song lyrics into structured 4-layer linguistic breakdowns with word-by-word glosses, literal translations, and idiomatic meanings.
---

# Song Lyric Breakdown (`/lyrics`)

Use this skill whenever the user types `/lyrics`, names a Hindi/Bollywood song, or asks to analyze song lyrics for vocabulary and grammar learning.

## Structural Format

1. **Song Sections:**
   - Group lyric lines cleanly using Markdown headers (`### Verse 1`, `### Chorus`, `### Hook`, `### Verse 2`).
   - Omit meaningless vocal fills (e.g. "ohohoh", "la la la") to keep the focus on linguistic value.

2. **4-Layer Line-by-Line Breakdown Template:**
   For every line, format strictly as follows:

   ```markdown
   * `[Romanized Hindi Lyric Line]`
     * Word-by-word breakdown: `[Word 1] ([Meaning 1]) | [Word 2] ([Meaning 2]) | [Word 3] ([Meaning 3])`
     * Literal translation: `"[Direct word-for-word translation]"`
     * Translation: `"[Natural, idiomatic English translation]"`
   ```

3. **Linguistic Commentary:**
   - Highlight poetic contractions or colloquial expressions (e.g. *tere bin* for *tere bina*, *akhiyan* for *aankhein*).
   - Point out grammatical parallels to curriculum concepts (e.g., Oblique shifts, postpositions, subjunctive mood).

4. **DIYA Hub Registration:**
   - Save the completed song breakdown as a structured JSON file in `diya/data/songs/[safe_slug].json` and update `diya/data/songs_index.json` so it appears immediately in the DIYA Song Lyrics library.
