# DIYA Hindi Web App — E2E Test Infrastructure (Tiers 1–4)

## 1. Test Philosophy & Architecture

The DIYA Acceptance Test Suite provides an **opaque-box, requirement-driven automated verification framework** ensuring all UX/UI enhancements, API contracts, data models, and integration flows adhere strictly to `ORIGINAL_REQUEST.md` and `PROJECT.md`.

### Core Verification Pillars
1. **Opaque-Box Contract Validation**: Testing interface contracts (inputs, outputs, side-effects, state mutations) rather than internal implementation details.
2. **Dual Track Orchestration**: Tests serve as executable specifications ahead of implementation. Unimplemented features fail cleanly during initial baseline runs and turn green as milestones complete.
3. **Multi-Layer Boundary Analysis**:
   - **Frontend React Invariants**: Verifying JSX exports, layout structure, Tailwind class compliance, portal rendering, event bindings, and library dependencies.
   - **Linguistic & Analytics Engine**: Direct ES module execution of `ankiLessonAnalytics.js` verifying mastery calculations, grade mappings, and gradient color formulas.
   - **Backend API & Persistence**: Live in-process HTTP server testing of Python `diya/server.py` endpoints, request/response schemas, error status codes, and roundtrip file persistence.
   - **Data Schemas**: Strict validation of `songs_index.json`, `stories_index.json`, `progress.json`, `deck_snapshot.json`, and `anki_queue.json`.

---

## 2. Test Hierarchy (Tiers 1–4)

```
========================================================================================
                              DIYA E2E ACCEPTANCE HARNESS
========================================================================================
  Tier 1: Feature Coverage (>=5 tests per feature, 21 features = 105 tests)
  ├── F1.1 - F1.9: General & Lessons Dashboard
  ├── F2.1 - F2.4: Stories UI Redesign
  ├── F3.1 - F3.5: Song Lyrics Experience
  └── F4.1 - F4.3: Learner Profile & Backend Persistence
----------------------------------------------------------------------------------------
  Tier 2: Boundary & Corner Cases (>=5 tests per feature, 21 features = 105 tests)
  ├── Clamped bounds (0%, 50%, 100%, >100% mastery gradient)
  ├── Zero cards, 4 cards deficit, 5 cards threshold, A0-00 reference exemptions
  ├── Missing fields, null URLs, 404 image fallbacks, malformed JSON bodies
  └── Offline Anki bridge resilience, queue failovers, and special character strings
----------------------------------------------------------------------------------------
  Tier 3: Cross-Feature Combinations (Pairwise Coverage = 20 tests)
  ├── Matrix of interactions across M1, M2, M3, and M4
  └── Integration contracts between frontend views, utilities, and backend storage
----------------------------------------------------------------------------------------
  Tier 4: Real-World Application Scenarios (5 Comprehensive Integration Scenarios)
  ├── Scenario 1: Complete Lesson Study & Card Inspection Session
  ├── Scenario 2: Story Reading & Full-Screen Reader Immersion
  ├── Scenario 3: Song Lyric Breakdown & Flashcard Creation Flow
  ├── Scenario 4: Learner Profile Customization & Diya Instruction Persistence
  └── Scenario 5: Offline Continuity & Queue Synchronization Resilience
========================================================================================
```

---

## 3. Feature Coverage Matrix

| Feature ID | Feature Name | Tier 1 Tests | Tier 2 Tests | Tier 3 Pairwise Tests | Tier 4 Scenarios |
|---|---|:---:|:---:|:---:|:---:|
| **F1.1** | Header Anki Pill (Connection Only) | 5 | 5 | T3.1, T3.5, T3.13, T3.20 | Scenario 1, Scenario 5 |
| **F1.2** | Catalog Mastery % Display | 5 | 5 | T3.3, T3.17 | Scenario 1, Scenario 5 |
| **F1.3** | Deficit Indicator (< 5 Cards) | 5 | 5 | T3.2, T3.17 | Scenario 1, Scenario 5 |
| **F1.4** | Green-to-Red Continuous Gradient | 5 | 5 | T3.1, T3.16 | Scenario 1 |
| **F1.5** | Grade Box Mastered/Learning/Struggling % | 5 | 5 | T3.3 | Scenario 1 |
| **F1.6** | Centered Inspect Modal via React Portal | 5 | 5 | T3.4 | Scenario 1 |
| **F1.7** | A0-00 Reference Lesson Exemption | 5 | 5 | T3.2, T3.16 | Scenario 1 |
| **F1.8** | Unboxed Summary Block with Yellow Accent | 5 | 5 | T3.4 | Scenario 1 |
| **F1.9** | Remove Deck Audit Menu | 5 | 5 | T3.5 | Scenario 1 |
| **F2.1** | Bookshelf Layout with Standing Covers | 5 | 5 | T3.6, T3.7 | Scenario 2 |
| **F2.2** | Book Cover Fallback (Deterministic Jewel Tone) | 5 | 5 | T3.6, T3.19 | Scenario 2 |
| **F2.3** | Full-Screen Viewer Separate Tab | 5 | 5 | T3.7, T3.8 | Scenario 2 |
| **F2.4** | Remove Inline Viewer Iframe | 5 | 5 | T3.8, T3.19 | Scenario 2 |
| **F3.1** | Song YouTube URL Field | 5 | 5 | T3.9, T3.18 | Scenario 3 |
| **F3.2** | Universal Media Player (YouTube & Spotify) | 5 | 5 | T3.9, T3.10 | Scenario 3 |
| **F3.3** | Genius-Style Plain Text Lyrics | 5 | 5 | T3.10, T3.11 | Scenario 3 |
| **F3.4** | Lyric Hover Modal (4-Layer Translations) | 5 | 5 | T3.11, T3.12 | Scenario 3 |
| **F3.5** | Lyric Add to Anki Editable Modal | 5 | 5 | T3.12, T3.13, T3.18 | Scenario 3, Scenario 5 |
| **F4.1** | "Other Languages I Know" Terminology | 5 | 5 | T3.14 | Scenario 4 |
| **F4.2** | Profile Rich Text Editors | 5 | 5 | T3.14, T3.15 | Scenario 4 |
| **F4.3** | Backend Persistence Bugfix (`custom_instructions`) | 5 | 5 | T3.15, T3.20 | Scenario 4 |

**Total Test Count:**
- Tier 1: 105 tests
- Tier 2: 105 tests
- Tier 3: 20 tests
- Tier 4: 5 scenarios
- **Grand Total: 235 automated tests**

---

## 4. Test Runner Invocation

The test suite is executable via standard Python 3 on Windows PowerShell without requiring third-party testing package installations:

### Run Complete Acceptance Suite (All Tiers 1–4)
```powershell
python scripts/e2e_acceptance_suite.py
```

### Run Specific Tiers
```powershell
# Run Tier 1 (Feature Coverage)
python scripts/e2e_acceptance_suite.py --tier 1

# Run Tier 2 (Boundary & Corner Cases)
python scripts/e2e_acceptance_suite.py --tier 2

# Run Tier 3 (Cross-Feature Combinations)
python scripts/e2e_acceptance_suite.py --tier 3

# Run Tier 4 (Real-World Integration Scenarios)
python scripts/e2e_acceptance_suite.py --tier 4
```

### Run Specific Feature Tests
```powershell
# Run all tests targeting F1.1 (Header Anki Pill)
python scripts/e2e_acceptance_suite.py --feature F1.1

# Run all tests targeting F4.3 (Backend Persistence)
python scripts/e2e_acceptance_suite.py --feature F4.3
```

### Advanced Options
```powershell
# Verbose output with full diagnostic traces
python scripts/e2e_acceptance_suite.py -v

# Generate machine-readable JSON execution report
python scripts/e2e_acceptance_suite.py --json-report test_results.json

# Stop on first failure
python scripts/e2e_acceptance_suite.py --fail-fast
```

---

## 5. Exit Codes & CI Integration

- `0`: All requested tests passed (100% green).
- `1`: One or more tests failed.
- `2`: Invalid command-line arguments or environment error.
