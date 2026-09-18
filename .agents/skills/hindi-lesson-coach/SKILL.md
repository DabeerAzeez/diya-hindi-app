---
name: hindi-lesson-coach
description: Teach sequential Hindi grammar lessons, run interactive quizzes with indented answers, format lessons using LaTeX formulas according to Lesson Summary Template, and sync summaries to Notion.
---

# Hindi Lesson Coach (`/lesson`)

Use this skill whenever the user types `/lesson`, requests the next sequential lesson, asks to review a previous lesson, or practices structured grammar.

## Execution Workflow

1. **Check Progress State:**
   - Read [memory/progress.json](../../../memory/progress.json) to retrieve `current_lesson_code` (e.g., `A1-07`), `mastered_patterns`, and `active_struggles`.
   - Read [hindi_curriculum_a0_to_a2.md](../../../hindi_curriculum_a0_to_a2.md) for the syllabus of that lesson.

2. **No Prompt Analysis Preceding Lesson:**
   - As per `GEMINI.md`, skip the Mandatory Prompt Analysis when `/lesson` is triggered. Begin directly with the lesson title.

3. **Format According to `resources/lesson_summary_template.md`:**
   - **Language Mode (Post-A1-08 Immersion Rule):**
     - For all lessons after `A1-08` (starting with `A1-09` through Level B1), **always deliver the lesson entirely in Romanized Hindi / Hinglish**.
     - All section summaries, conceptual explanations, subheadings, grammar mechanics, dialogue lines, teacher guidance from Diya, and quiz prompts must be written directly in natural Romanized Hindi (e.g., *"Is lesson mein hum seekhenge...", "Dhyan rahe ki...", "Formula dekho...", "Quiz ke sawaal:"*).
     - English may only be used for short vocabulary glosses/parentheticals where introducing brand new words, English target sentences in the quiz, or if the student explicitly asks for an English explanation.
     - Devanagari remains reference-only (never quiz or mandate reading/writing in Devanagari).
   - **High-Level Section Structure (Strict Sequence):**
     1. `# 🌟Summary`
        - High-level overview of the lesson's main themes, conversational utility, and polyglot parallels (e.g. Tamil postpositions or French/Spanish structures) — written in Romanized Hindi for post-A1-08 lessons.
        - Include LaTeX grammar equations enclosed in `$$` delimiters for Notion compatibility, e.g.:
          `$$\text{Subject} + \text{ko} + \text{Object} + \text{chaahiye}$$`
     2. `# 📘Lesson`
        - Clear subheadings with emojis in Romanized Hindi (e.g. `## 🏷️ 1. Discourse Markers aur Fillers kaa Use`).
        - Concise explanation, high-frequency spoken examples, and natural Hinglish usage.
        - Keep male speaker endings locked for the student (`-taa hoon`, `-aa / gayaa`, `-\bar{u}\dot{n}gaa`).
     3. `# 🎭Dialogue Example`
        - Contextual, natural spoken dialogue positioned immediately before the quiz.
        - Sets a relatable real-life scene (e.g. Norwich pub/cafe catch-up with Shivani, Toronto tech workplace/coffee run, music practice, improv banter).
        - Consists of 4–8 authentic conversational exchanges demonstrating how the newly learned grammar structures, vocabulary, discourse fillers, and emotional tones come alive in spontaneous dialogue.
        - Formatted with clean speaker labels:
          ```markdown
          - **[Speaker 1]:** *"[Romanized dialogue line]"*
          - **[Speaker 2]:** *"[Romanized dialogue line]"*
          ```
     4. `# ❓Quiz`
        - **Concept & Grammar Questions:** 2–3 questions testing rules or mechanics, asked in Romanized Hindi.
        - **Translation Questions:** 5–10 practical sentence translations (Hinglish $\leftrightarrow$ English) featuring relatable contexts (Toronto, music, AI work, Shivani / Norwich).
        - **Indentation Rule:** Bullet points for answers MUST be indented one level under the questions:
          ```markdown
          1. **[English Sentence] (informal, m)**
             - **Answer:** `[Romanized Hindi]` — [Devanagari]
               <small>[Word-by-word breakdown]</small>
          ```

4. **Update Memory & Save to DIYA Hub:**
   - After conducting the lesson or upon student completion, update `memory/progress.json` with newly mastered concepts or active struggles.
   - Save the completed lesson summary directly as a Markdown file in `diya/data/lessons/` (e.g., `lesson_a2-01__compound_verbs.md`) and structured JSON in `diya/data/lessons/` for immediate display in the DIYA web application.
