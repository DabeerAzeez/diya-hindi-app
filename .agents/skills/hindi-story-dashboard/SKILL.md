---
name: hindi-story-dashboard
description: Generate immersive, full-screen bilingual E-reader story dashboards with two-page book spreads, deluxe cover page, synchronized sentence alignment, guaranteed hover diacritics, and Hinglish comprehension checks.
---

# Hindi Story Dashboard & E-Reader (`/story`)

Use this skill whenever the user types `/story`, asks for reading practice, or requests a story dashboard / novel.

## 1. Architectural Principles & Layout
Every story generated under this skill must be built as a **full-screen, immersive E-Reader Application** (occupying 100vh and >90% of screen space) rather than a continuous scrolling webpage:

1. **Full-Viewport App Shell:**
   - Container takes full viewport height (`height: 100vh; width: 100vw; overflow: hidden;`).
   - The central **Open Book Desk** occupies >90% of the screen width and height.
   - Designed with realistic physical book aesthetics: central spine gutter shadow, soft drop shadows, page borders, running headers, and running footers with page numbers.
   - **Zero-Flicker Instant Turns:** Remove page-turn animations or transitions that cause layout flickering; spread updates should render cleanly and instantaneously.

2. **Authentic Closed Book Cover (Spread 0):**
   - When the book is closed on Spread 0:
     - The left side of the screen must be **completely empty** (`visibility: hidden; opacity: 0; pointer-events: none; border: none; background: transparent; box-shadow: none;`).
     - The central spine divider is hidden (`visibility: hidden; opacity: 0; pointer-events: none;`).
     - The **Cover Page sits on the right side only** using explicit grid positioning (`grid-column: 3;`), presenting an authentic closed hardcover book aesthetic with rich borders and depth shadows.
     - **Grid Slotting Precaution:** Always declare `#pageLeft { grid-column: 1; }`, `#spineDivider { grid-column: 2; }`, and `#pageRight { grid-column: 3; }` with `grid-template-columns: 1fr 14px 1fr;` to prevent the browser from inadvertently squishing the cover into the 14px center column.
     - Content on cover: Only the book title in large display font, subtitle, and author's name (`Diya`).
     - **No "Begin Reading" buttons** and **no frontispiece page**—clicking the cover, pressing Right Arrow / Space, or clicking the floating turn arrow turns to Page 1. The left turn arrow is disabled on Spread 0.

3. **Typography Standards: Sans-Serif UI vs. Consistent Serif Book Interior:**
   - **General UI Elements (Modern Sans-Serif):** Top bar, buttons (`.pill-btn`, `.icon-btn`, font scalers, view toggles), bottom status bar, reading progress track, turn arrows (`‹`, `›`), Table of Contents side drawer, linguistic guide, and hover tooltip popups (`.word::after`) use system sans-serif:
     `font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;`
   - **The Book Itself (Classic Book Serif):** All book elements—running headers, chapter titles, body paragraphs, sentences, words, diacritic text, image captions, page footers, and the entire cover page—use an authentic, consistent serif typeface:
     `font-family: "Georgia", "Cambria", "Times New Roman", "Source Serif Pro", serif;`

4. **Discrete Page Content Consistency & Vertical Scrollbar Rules:**
   - The book is divided into fixed discrete numbered pages (e.g., Pages 1 to 6) pre-computed in JSON objects (`pagesHindi` and `pagesEnglish`).
   - **Identical Content per Page:** When switching between **Novel Spread** and **Bilingual Spread**, each numbered page MUST contain the exact same sentences. Page 1 never stretches or absorbs content from Page 2.
   - **Mode A: Bilingual Spread:**
     - Left Page = Page $N$ in Romanized Hindi (`#contentLeft`).
     - Right Page = Page $N$ in Natural English translation (`#contentRight`).
     - **Matching Page Numbers:** Both left and right page footers display the **SAME page number** (e.g. `— 1 —` on left, `— 1 —` on right).
   - **Mode B: Novel Spread (Single Language - Hindi):**
     - Left Page = Page $N$ (e.g. Page 1, footer `— 1 —`).
     - Right Page = Page $N+1$ (e.g. Page 2, footer `— 2 —`).
   - **Strict Scrollbar Standards:**
     - **Hindi Side (NEVER Scrolls):** Hindi content on the left page (bilingual) or both pages (novel) must **NEVER** have a vertical scrollbar (`overflow: hidden !important;`).
     - **Page Fill Height Calibration:** The narrative per page must be sufficiently rich (~14-16 sentences across 3 paragraphs for non-image pages, ~11-12 sentences across 2 paragraphs + 180px illustration for image pages) with `--line-height: 1.82` and `--font-scale: 1.02rem` so that at default font size the Hindi content extends gracefully down to the bottom of the page near the footer line, never stopping awkwardly halfway down.
     - **English Side (Scrollable when needed):** In Bilingual Spread, the English facing page may have a subtle custom scrollbar (`overflow-y: auto !important;`) if the English translation text runs longer than the page height.

5. **Minimalist, Single Chapter Headings (No AI Clutter):**
   - Chapter titles appear **only once** at the top of chapter start pages in a large, elegant book font.
   - Do NOT repeat chapter numbers (no running badges, no "Chapter 1 • Part 1", no "Chapter 1 • The Setup").
   - In Novel Spread, the heading appears in Hindi. In Bilingual Spread, the English page shows the heading in English.
   - Do NOT include labels like "Parallel English Translation", "Synchronized line-by-line", or language tags. Keep it looking like an authentic published novel.

6. **Sleek Minimal Top App Bar (Distraction-Free):**
   - **Left:** `☰` Drawer toggle button $+$ Book Title.
   - **Right:** 
     - `📖 View Mode` toggle (Bilingual Spread vs. Novel Spread).
     - `🔤 Diacritics` text toggle (toggles diacritics in main body text).
     - `A-` / `A+` font size scaler buttons.
   - *Note:* Keep the header bar clean—do NOT clutter with color theme switchers or central chapter badge pills.

7. **Collapsible Side Drawer (`☰` Menu):**
   - Opens on clicking `☰` or pressing `Esc`.
   - Contains:
     - **Table of Contents:** Direct jump links to Cover Page and all chapters with page numbers.
     - **Linguistic Legend:** Pronunciation guide for long vowels (`ā, ī, ū`), retroflex consonants (`ṭ, ḍ, ṛ`), nasals (`ñ`), and TTS audio instructions.

---

## 2. Linguistic Protocols & Diacritics Standard

1. **Guaranteed Diacritics on Hover Menu (Strict Rule):**
   - Hovering over ANY Hindi word in the story MUST display a double-deck tooltip containing:
     - Line 1: English meaning
     - Line 2: Bracketed phonetic pronunciation in **exact IAST diacritics** with macrons and retroflex consonants!
   - Tooltip format: `data-tooltip="meaning&#10;[[diacritic]]"` (e.g. `crowd [f]&#10;[bhīṛ]`, `small [m]&#10;[choṭā]`, `envelope [m]&#10;[lifāfā]`).
   - The hover menu must ALWAYS show diacritics, regardless of whether the body text diacritic toggle is active or not.

2. **Young Adult (YA) Narrative Depth:**
   - Avoid trivial, babyish, or overly brief texts.
   - Write stories with genuine **Young Adult novel pacing** (~40+ sentences per chapter, ~120+ sentences across 3 chapters).
   - Incorporate sensory scene descriptions, witty banter, internal monologue, emotional beats, and engaging mystery or adventure plots outside the student's daily bubble.

3. **Synchronized Bilingual Highlighting (`data-sid`):**
   - Every sentence is tagged with matching IDs across both languages (`data-sid="p1-s1"`, etc.).
   - Hovering over a sentence in either language synchronously highlights its counterpart.

4. **Native Browser Speech Synthesis (TTS):**
   - Every Hindi sentence includes an inline `🔊` audio button triggering `window.speechSynthesis` with `hi-IN` language voice pack at rate `0.88`.

5. **Script Policy:**
   - 100% Romanized Hindi with IAST diacritics. Never quiz or require reading in Devanagari script.

---

## 3. Visual Story Assets & DIYA Hub Registration
- Include at least 3 AI-generated scene illustrations positioned at key narrative turning points in each chapter.
- Save assets to `diya/data/stories/assets/` (and `stories/assets/`) and embed them inside clean, responsive `<figure>` frames with bilingual captions.
- Save the completed HTML story file to `diya/data/stories/` and register the story entry in `diya/data/stories_index.json` so it appears immediately in the DIYA web application.
- Cap image container max-height at 180px to leave plenty of room for narrative text to extend to the bottom of the page.

---

## 4. Comprehension Check in Chat
After generating and linking the story dashboard:
1. Present **3 concise comprehension questions in Hinglish** directly in the chat.
2. Direct the student to answer in Hinglish or English.
3. Validate answers with encouraging feedback and gentle grammatical coaching using the Prompt Analysis standard.
