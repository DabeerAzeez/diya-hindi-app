# TEST_READY: DIYA Acceptance Test Suite (Tiers 1–4)

**Status:** READY & OPERATIONAL  
**Date:** 2026-09-16  
**Test Harness:** `scripts/e2e_acceptance_suite.py`  
**Test Infra Documentation:** `TEST_INFRA.md`  

---

## 1. Executive Summary

The comprehensive, requirement-driven acceptance test suite for the DIYA Hindi Web App has been designed, implemented, and validated. The suite provides rigorous, opaque-box verification spanning **Tiers 1–4** across all 21 features defined in `PROJECT.md` and `ORIGINAL_REQUEST.md`.

### Baseline Execution Summary
- **Total Tests Executed:** 235 automated tests
- **Passing Baseline:** 184 passed (78.3%)
- **Failing Baseline (Expected Ahead of Implementation):** 51 tests
- **Zero-Dependency Runner:** Runs directly via Python 3 on Windows PowerShell without requiring external test runner dependencies.
- **Cross-Platform Bridge:** Integrates with local Node runtime for direct ES module execution of linguistic/analytics algorithms and spins up an ephemeral in-process test server for live HTTP API contract testing.

---

## 2. Test Suite Composition

| Tier | Tier Scope | Total Tests | Baseline Passed | Baseline Failed | Purpose |
|---|---|:---:|:---:|:---:|---|
| **Tier 1** | Feature Coverage | 105 | 75 | 30 | >= 5 tests per feature (F1.1 – F4.3) verifying primary happy path contracts |
| **Tier 2** | Boundary & Corner Cases | 105 | 94 | 11 | Stress testing, null/empty inputs, zero cards, 4 vs 5 thresholds, clamping, offline failover |
| **Tier 3** | Cross-Feature Combinations | 20 | 13 | 7 | Pairwise interaction matrix across M1, M2, M3, and M4 modules |
| **Tier 4** | Real-World Application Scenarios | 5 | 2 | 3 | Full multi-step end-to-end user journeys (Study, Reader, Songs, Profile, Offline) |
| **Total** | **All Tiers** | **235** | **184** | **51** | **Comprehensive Acceptance Harness** |

---

## 3. How to Run the Tests

The test runner can be executed at any time from Windows PowerShell in the project root:

```powershell
# Run the complete test suite (all 235 tests across Tiers 1-4)
python scripts/e2e_acceptance_suite.py

# Run a specific tier
python scripts/e2e_acceptance_suite.py --tier 1
python scripts/e2e_acceptance_suite.py --tier 2
python scripts/e2e_acceptance_suite.py --tier 3
python scripts/e2e_acceptance_suite.py --tier 4

# Run all tests for a specific feature
python scripts/e2e_acceptance_suite.py --feature F1.1
python scripts/e2e_acceptance_suite.py --feature F2.3
python scripts/e2e_acceptance_suite.py --feature F3.5
python scripts/e2e_acceptance_suite.py --feature F4.3

# Run with verbose output (shows every test ID, name, and assertion result)
python scripts/e2e_acceptance_suite.py -v

# Generate machine-readable JSON results file
python scripts/e2e_acceptance_suite.py --json-report baseline_test_results.json
```

---

## 4. Defect Escalation Report (For Implementing Agents)

During test suite implementation and initial baseline execution, the following implementation bugs and contracts were identified:

1. **Bug: `diya/server.py` Profile Persistence Desynchronization (F4.3)**
   - **File:** `diya/server.py` lines 376 vs 426
   - **Observation:** `GET /api/profile` reads `prog.get('learning_strategy', {}).get('approach')`, while `POST /api/profile` writes to `prog['learning_strategy']['custom_instructions']`.
   - **Impact:** Custom system instructions saved by the student in the Profile Drawer are overwritten on page reload by the hardcoded default approach string.
   - **Test Coverage:** `T1_F4.3_profile_roundtrip_persistence`, `T3_T3.15_rich_text_html_persists_via_custom_instructions_fix`.

2. **Corner-Case Bug: Null Pointer in `getCardsForLesson` (`frontend/src/utils/ankiLessonAnalytics.js`)**
   - **File:** `frontend/src/utils/ankiLessonAnalytics.js` line 71
   - **Observation:** `cards.filter((c) => { if (Array.isArray(c.lesson_codes)) ... })` does not check `if (!c) return false;`. If the cards array contains any `null` or `undefined` item, it throws `TypeError: Cannot read properties of null (reading 'lesson_codes')`.
   - **Impact:** Crashes lesson card computation if corrupt card data or null records enter the system.
   - **Test Coverage:** `T2_F1.2_corrupt_card_records_resilience`.

---

## 5. Next Steps for Milestone Workers

As worker agents complete milestones:
- **Milestone 1 (General & Lessons Dashboard):** Run `python scripts/e2e_acceptance_suite.py --tier 1 --feature F1.1` through `F1.9`.
- **Milestone 2 (Stories UI Redesign):** Run `python scripts/e2e_acceptance_suite.py --feature F2.1` through `F2.4`.
- **Milestone 3 (Song Lyrics Experience):** Run `python scripts/e2e_acceptance_suite.py --feature F3.1` through `F3.5`.
- **Milestone 4 (Learner Profile Rich Text):** Run `python scripts/e2e_acceptance_suite.py --feature F4.1` through `F4.3`.
- **Final Verification:** Run `python scripts/e2e_acceptance_suite.py` to verify 100% green pass rate (235/235).
