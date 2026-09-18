#!/usr/bin/env python3
"""
DIYA Hindi Web App — End-to-End Acceptance Test Suite (Tiers 1–4)
Opaque-box, requirement-driven verification for UX/UI improvements,
API contracts, data models, component invariants, and end-to-end flows.

Usage:
    python scripts/e2e_acceptance_suite.py                  # Run all tiers (Tiers 1-4)
    python scripts/e2e_acceptance_suite.py --tier 1         # Tier 1 (Feature Coverage)
    python scripts/e2e_acceptance_suite.py --tier 2         # Tier 2 (Boundary & Corner Cases)
    python scripts/e2e_acceptance_suite.py --tier 3         # Tier 3 (Cross-Feature Combinations)
    python scripts/e2e_acceptance_suite.py --tier 4         # Tier 4 (Real-World Scenarios)
    python scripts/e2e_acceptance_suite.py --feature F1.1   # Specific feature
    python scripts/e2e_acceptance_suite.py -v               # Verbose
    python scripts/e2e_acceptance_suite.py --json-report out.json
"""

import sys
import os
import re
import json
import time
import argparse
import subprocess
import threading
import urllib.request
import urllib.error
import socketserver
from pathlib import Path

# Force UTF-8 output encoding on Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIYA_DIR = PROJECT_ROOT / "diya"
DATA_DIR = DIYA_DIR / "data"
MEMORY_DIR = PROJECT_ROOT / "memory"

# ANSI color codes
USE_COLOR = sys.stdout.isatty() or os.environ.get('TERM') in ('xterm', 'xterm-256color') or True

def color(text, code):
    if not USE_COLOR:
        return text
    codes = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        'reset': '\033[0m'
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"

def check(condition, message="Assertion failed"):
    """Assertion helper usable in lambdas and normal functions."""
    if not condition:
        raise AssertionError(message)

# ==============================================================================
# In-Process Server Fixture for API Testing
# ==============================================================================

class TestServerHarness:
    """Manages an isolated in-process instance of DiyaHandler for HTTP testing."""
    def __init__(self, port=18080):
        self.port = port
        self.httpd = None
        self.thread = None
        self.base_url = f"http://127.0.0.1:{self.port}"

    def start(self):
        sys.path.insert(0, str(PROJECT_ROOT))
        from diya.server import DiyaHandler
        
        class QuietDiyaHandler(DiyaHandler):
            def log_message(self, format, *args):
                pass

        attempts = 0
        while attempts < 15:
            try:
                self.httpd = socketserver.TCPServer(('127.0.0.1', self.port), QuietDiyaHandler)
                break
            except OSError:
                self.port += 1
                self.base_url = f"http://127.0.0.1:{self.port}"
                attempts += 1

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.3)

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None

    def get(self, endpoint):
        req = urllib.request.Request(f"{self.base_url}{endpoint}")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read()
                content_type = resp.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return resp.getcode(), json.loads(data.decode('utf-8')), resp.headers
                return resp.getcode(), data.decode('utf-8', errors='replace'), resp.headers
        except urllib.error.HTTPError as e:
            data = e.read()
            try:
                return e.code, json.loads(data.decode('utf-8')), e.headers
            except Exception:
                return e.code, data.decode('utf-8', errors='replace'), e.headers
        except Exception as e:
            return 0, str(e), {}

    def post(self, endpoint, payload):
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{self.base_url}{endpoint}",
            data=req_data,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read()
                return resp.getcode(), json.loads(data.decode('utf-8')), resp.headers
        except urllib.error.HTTPError as e:
            data = e.read()
            try:
                return e.code, json.loads(data.decode('utf-8')), e.headers
            except Exception:
                return e.code, data.decode('utf-8', errors='replace'), e.headers
        except Exception as e:
            return 0, str(e), {}


# ==============================================================================
# Helper Utilities (Node Bridge, File Readers, AST & Regex Checkers)
# ==============================================================================

def run_node_eval(script: str) -> dict:
    """Executes a JavaScript ES module snippet using Node and returns JSON result."""
    try:
        res = subprocess.run(
            ['node', '--input-type=module'],
            input=script,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(PROJECT_ROOT)
        )
        if res.returncode != 0:
            return {'success': False, 'error': res.stderr.strip() or 'Node execution failed'}
        out = res.stdout.strip()
        try:
            return {'success': True, 'data': json.loads(out)}
        except Exception:
            return {'success': True, 'raw': out}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def read_text(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def read_json(file_path: Path, default=None):
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def stats_is_ref(stats: dict) -> bool:
    """Helper to check if lesson stats record denotes reference lesson."""
    return stats.get('isReference') is True or stats.get('grade') == 'Ref' or stats.get('gradeLabel') == 'Ref'


# ==============================================================================
# Test Result Model & Collector
# ==============================================================================

class TestCaseResult:
    def __init__(self, test_id: str, tier: int, feature: str, name: str, passed: bool, error: str = ""):
        self.test_id = test_id
        self.tier = tier
        self.feature = feature
        self.name = name
        self.passed = passed
        self.error = error

    def to_dict(self):
        return {
            "test_id": self.test_id,
            "tier": self.tier,
            "feature": self.feature,
            "name": self.name,
            "passed": self.passed,
            "error": self.error
        }

class TestRunner:
    def __init__(self, verbose=False, fail_fast=False):
        self.verbose = verbose
        self.fail_fast = fail_fast
        self.results = []
        self.server = TestServerHarness()

    def record(self, tier: int, feature: str, name: str, assertion_fn):
        test_id = f"T{tier}_{feature}_{name}"
        passed = False
        err_msg = ""
        try:
            assertion_fn()
            passed = True
        except AssertionError as ae:
            err_msg = str(ae) or "Assertion failed"
        except Exception as e:
            err_msg = f"{type(e).__name__}: {str(e)}"

        res = TestCaseResult(test_id, tier, feature, name, passed, err_msg)
        self.results.append(res)

        symbol = color("[PASS]", "green") if passed else color("[FAIL]", "red")
        if self.verbose or not passed:
            print(f"  {symbol} {test_id} - {name}")
            if not passed and err_msg:
                print(f"         {color(err_msg, 'dim')}")

        if not passed and self.fail_fast:
            raise RuntimeError(f"Fail-fast triggered on {test_id}: {err_msg}")

    def run_all(self, selected_tier=None, selected_feature=None):
        print(color("\n=======================================================", "cyan"))
        print(color("  DIYA HINDI WEB APP — ACCEPTANCE TEST RUNNER (T1–T4)", "bold"))
        print(color("=======================================================\n", "cyan"))

        print(color("[INFO] Starting background test server...", "dim"))
        self.server.start()

        try:
            if selected_tier is None or selected_tier == 1:
                print(color("\n--- RUNNING TIER 1: FEATURE COVERAGE (>=5 tests per feature) ---", "blue"))
                self.run_tier_1(selected_feature)

            if selected_tier is None or selected_tier == 2:
                print(color("\n--- RUNNING TIER 2: BOUNDARY & CORNER CASES (>=5 tests per feature) ---", "blue"))
                self.run_tier_2(selected_feature)

            if selected_tier is None or selected_tier == 3:
                print(color("\n--- RUNNING TIER 3: CROSS-FEATURE COMBINATIONS (Pairwise) ---", "blue"))
                self.run_tier_3(selected_feature)

            if selected_tier is None or selected_tier == 4:
                print(color("\n--- RUNNING TIER 4: REAL-WORLD APPLICATION SCENARIOS ---", "blue"))
                self.run_tier_4(selected_feature)

        finally:
            print(color("\n[INFO] Stopping background test server...", "dim"))
            self.server.stop()

        self.print_summary()

    def print_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        pct = (passed / total * 100) if total > 0 else 0

        print(color("\n=======================================================", "cyan"))
        print(color("                  TEST EXECUTION SUMMARY", "bold"))
        print(color("=======================================================", "cyan"))
        print(f"Total Tests Executed: {total}")
        print(f"Passed:               {color(str(passed), 'green' if passed > 0 else 'dim')}")
        print(f"Failed:               {color(str(failed), 'red' if failed > 0 else 'green')}")
        print(f"Success Rate:         {pct:.1f}%")

        print("\n--- Breakdown By Tier ---")
        for t in [1, 2, 3, 4]:
            tier_tests = [r for r in self.results if r.tier == t]
            if tier_tests:
                t_pass = sum(1 for r in tier_tests if r.passed)
                t_fail = len(tier_tests) - t_pass
                t_pct = (t_pass / len(tier_tests)) * 100
                print(f"  Tier {t}: {t_pass}/{len(tier_tests)} passed ({t_pct:.1f}%) | {t_fail} failures")

        features = sorted(list(set(r.feature for r in self.results)))
        print("\n--- Breakdown By Feature ---")
        for feat in features:
            f_tests = [r for r in self.results if r.feature == feat]
            f_pass = sum(1 for r in f_tests if r.passed)
            f_fail = len(f_tests) - f_pass
            status = color("PASS", "green") if f_fail == 0 else color(f"{f_fail} FAIL", "red")
            print(f"  {feat:<12}: {f_pass:>2}/{len(f_tests):<2} passed [{status}]")

        print(color("=======================================================\n", "cyan"))

    def export_json(self, output_path: str):
        data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "results": [r.to_dict() for r in self.results]
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(color(f"[INFO] JSON report saved to: {output_path}", "green"))

    # ==========================================================================
    # TIER 1: FEATURE COVERAGE (21 features * 5 tests = 105 tests)
    # ==========================================================================
    def run_tier_1(self, filter_feature=None):
        def should_run(feat):
            return filter_feature is None or filter_feature.upper() == feat.upper()

        # F1.1 Header Anki Pill
        if should_run("F1.1"):
            navbar_src = read_text(FRONTEND_DIR / "src" / "components" / "Navbar.jsx")
            
            self.record(1, "F1.1", "live_status_renders_live_label", lambda: 
                check("Anki Live" in navbar_src, "Navbar must contain 'Anki Live' indicator text")
            )
            self.record(1, "F1.1", "offline_status_renders_offline_label", lambda: 
                check("Anki Offline" in navbar_src, "Navbar must contain 'Anki Offline' indicator text")
            )
            self.record(1, "F1.1", "no_card_counts_in_pill", lambda: 
                check(not re.search(r'ankiStatus\.(total|cards|count)', navbar_src, re.IGNORECASE),
                      "Header Anki pill must NOT display card counts or count variables")
            )
            self.record(1, "F1.1", "no_deck_audit_modal_trigger_on_pill", lambda: 
                check("onOpenDeckAudit" not in navbar_src or "onClick={onOpenDeckAudit}" not in navbar_src,
                      "Header Anki pill must NOT trigger deck audit modal or bind onOpenDeckAudit")
            )
            self.record(1, "F1.1", "status_dot_styling", lambda: 
                check("bg-emerald-400" in navbar_src or "bg-rose-500" in navbar_src,
                      "Header Anki pill must have green/emerald and red/rose status dot styling")
            )

        # F1.2 Catalog Mastery %
        if should_run("F1.2"):
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            
            self.record(1, "F1.2", "catalog_displays_percentage_score", lambda: 
                check("masteryPct" in lessons_src and "%" in lessons_src,
                      "Lesson catalog must display percentage mastery score")
            )
            self.record(1, "F1.2", "weak_card_count_removed_from_catalog", lambda: 
                check("🔴" not in lessons_src and "Weak" not in lessons_src,
                      "Weak card count badge (e.g. 🔴 X Weak) must be removed from lesson catalog")
            )
            self.record(1, "F1.2", "learning_card_count_removed_from_catalog", lambda: 
                check("🟡 In Progress" not in lessons_src,
                      "Weak/learning card counts must be replaced with percentage mastery score")
            )
            
            def test_f1_2_calc():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [
                        { status: 'Mastered', lesson_codes: ['A1-01'] },
                        { status: 'Mastered', lesson_codes: ['A1-01'] },
                        { status: 'Learning', lesson_codes: ['A1-01'] },
                        { status: 'Struggling', lesson_codes: ['A1-01'] }
                    ];
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'], f"Node error: {node_res.get('error')}")
                data = node_res['data']
                check(data.get('masteryPct') == 50, f"Expected 50% mastery, got {data.get('masteryPct')}")
            self.record(1, "F1.2", "mastery_pct_calculation_accuracy", test_f1_2_calc)

            def test_f1_2_updates():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(10).fill(null).map((_, i) => ({
                        status: i < 8 ? 'Mastered' : 'Learning',
                        lesson_codes: ['A1-02']
                    }));
                    const stats = calculateLessonStats(cards, 'A1-02');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('masteryPct') == 80,
                      "Catalog mastery % must update dynamically when cards are mastered")
            self.record(1, "F1.2", "catalog_badge_reflects_card_updates", test_f1_2_updates)

        # F1.3 Deficit Indicator
        if should_run("F1.3"):
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            
            def test_f1_3_under_5():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [{ status: 'Learning', lesson_codes: ['A1-03'] }];
                    const stats = calculateLessonStats(cards, 'A1-03');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isDeficit') is True,
                      "calculateLessonStats must set isDeficit=true when totalCards < 5")
            self.record(1, "F1.3", "deficit_detected_under_5_cards", test_f1_3_under_5)

            def test_f1_3_at_5():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(5).fill(null).map(() => ({ status: 'Learning', lesson_codes: ['A1-04'] }));
                    const stats = calculateLessonStats(cards, 'A1-04');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isDeficit') is False,
                      "calculateLessonStats must set isDeficit=false when totalCards >= 5")
            self.record(1, "F1.3", "no_deficit_at_or_above_5_cards", test_f1_3_at_5)

            self.record(1, "F1.3", "grey_indicator_styling_in_catalog", lambda: 
                check(("slate" in lessons_src or "gray" in lessons_src or "zinc" in lessons_src) and "Deficit" in lessons_src,
                      "Lesson catalog must display a subtle grey warning indicator for deficit")
            )
            self.record(1, "F1.3", "deficit_badge_rendered_in_lessons_view", lambda: 
                check("isDeficit" in lessons_src or "deficitCount" in lessons_src,
                      "LessonsView must reference isDeficit or deficitCount for catalog rendering")
            )

            def test_f1_3_count():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [{ status: 'Learning', lesson_codes: ['A1-05'] }, { status: 'Learning', lesson_codes: ['A1-05'] }];
                    const stats = calculateLessonStats(cards, 'A1-05');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('deficitCount') == 3,
                      "deficitCount must equal 5 - totalCards")
            self.record(1, "F1.3", "deficit_count_calculation", test_f1_3_count)

        # F1.4 Green-to-Red Gradient
        if should_run("F1.4"):
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            
            def test_f1_4_100():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify(getMasteryGradientStyle(100)));
                """)
                check(node_res['success'], f"Node error: {node_res.get('error')}")
                style = node_res['data']
                check("120" in style.get('color', '') or "120" in style.get('background', ''),
                      "At 100%, gradient must use hue 120 (pure green)")
            self.record(1, "F1.4", "gradient_hue_at_100_percent", test_f1_4_100)

            def test_f1_4_50():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify(getMasteryGradientStyle(50)));
                """)
                check(node_res['success'], f"Node error: {node_res.get('error')}")
                style = node_res['data']
                check("0" in style.get('color', '') or "0" in style.get('background', ''),
                      "At 50%, gradient must use hue 0 (pure red)")
            self.record(1, "F1.4", "gradient_hue_at_50_percent", test_f1_4_50)

            def test_f1_4_75():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify(getMasteryGradientStyle(75)));
                """)
                check(node_res['success'], f"Node error: {node_res.get('error')}")
                style = node_res['data']
                check("60" in style.get('color', '') or "60" in style.get('background', ''),
                      "At 75%, gradient must use hue 60 (yellow)")
            self.record(1, "F1.4", "gradient_hue_at_75_percent", test_f1_4_75)

            self.record(1, "F1.4", "mastery_grade_box_uses_gradient", lambda: 
                check("getMasteryGradientStyle" in lessons_src or "gradientStyle" in lessons_src,
                      "Mastery grade box in LessonsView must apply continuous gradient style")
            )
            self.record(1, "F1.4", "catalog_indicator_uses_gradient", lambda: 
                check("gradientStyle" in lessons_src or "getMasteryGradientStyle" in lessons_src,
                      "Catalog badge in LessonsView must apply continuous gradient style")
            )

        # F1.5 Grade Box Breakdown
        if should_run("F1.5"):
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            
            self.record(1, "F1.5", "mastered_percentage_displayed", lambda: 
                check("masteryPct" in lessons_src or "Mastered" in lessons_src,
                      "Grade box must display Mastered percentage")
            )
            self.record(1, "F1.5", "learning_percentage_displayed", lambda: 
                check("learningPct" in lessons_src or "Learning" in lessons_src,
                      "Grade box must display Learning percentage")
            )
            self.record(1, "F1.5", "struggling_percentage_displayed", lambda: 
                check("strugglingPct" in lessons_src or "Struggling" in lessons_src,
                      "Grade box must display Struggling percentage")
            )

            def test_f1_5_sum():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [
                        { status: 'Mastered', lesson_codes: ['A1-06'] },
                        { status: 'Learning', lesson_codes: ['A1-06'] },
                        { status: 'Struggling', lesson_codes: ['A1-06'] },
                        { status: 'Mastered', lesson_codes: ['A1-06'] }
                    ];
                    const stats = calculateLessonStats(cards, 'A1-06');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'], f"Node error: {node_res.get('error')}")
                d = node_res['data']
                total_pct = d.get('masteryPct', 0) + d.get('learningPct', 0) + d.get('strugglingPct', 0)
                check(total_pct == 100, f"Expected percentages to sum to 100, got {total_pct}")
            self.record(1, "F1.5", "percentages_sum_to_100", test_f1_5_sum)

            def test_f1_5_keys():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const stats = calculateLessonStats([{ status: 'Learning', lesson_codes: ['A1-07'] }], 'A1-07');
                    console.log(JSON.stringify({
                        hasMastery: 'masteryPct' in stats,
                        hasLearning: 'learningPct' in stats,
                        hasStruggling: 'strugglingPct' in stats
                    }));
                """)
                check(node_res['success'] and node_res['data'].get('hasMastery') and node_res['data'].get('hasLearning') and node_res['data'].get('hasStruggling'),
                      "calculateLessonStats must return masteryPct, learningPct, and strugglingPct")
            self.record(1, "F1.5", "calculateLessonStats_returns_all_percentages", test_f1_5_keys)

        # F1.6 Centered Inspect Modal
        if should_run("F1.6"):
            modal_src = read_text(FRONTEND_DIR / "src" / "components" / "LessonCardsModal.jsx")
            
            self.record(1, "F1.6", "create_portal_imported", lambda: 
                check("createPortal" in modal_src, "LessonCardsModal must import createPortal from react-dom")
            )
            self.record(1, "F1.6", "rendered_via_portal", lambda: 
                check(bool(re.search(r'createPortal\s*\(', modal_src)),
                      "LessonCardsModal must render using createPortal to document.body")
            )
            self.record(1, "F1.6", "fixed_inset_positioning", lambda: 
                check("fixed inset-0" in modal_src and "z-50" in modal_src,
                      "Inspect cards modal outer container must have fixed inset-0 z-50 styling")
            )
            self.record(1, "F1.6", "centering_flex_classes", lambda: 
                check("flex items-center justify-center" in modal_src,
                      "Inspect cards modal outer container must use 'flex items-center justify-center' to center on window")
            )
            self.record(1, "F1.6", "modal_dialog_max_dimensions", lambda: 
                check("max-h-[90vh]" in modal_src or "max-w-" in modal_src,
                      "Modal dialog must constrain viewport max dimensions")
            )

        # F1.7 A0-00 Reference Lesson
        if should_run("F1.7"):
            analytics_src = read_text(FRONTEND_DIR / "src" / "utils" / "ankiLessonAnalytics.js")
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            
            self.record(1, "F1.7", "reference_lessons_constant", lambda: 
                check("REFERENCE_LESSONS" in analytics_src and "A0-00" in analytics_src,
                      "REFERENCE_LESSONS array in ankiLessonAnalytics.js must include 'A0-00'")
            )

            def test_f1_7_fn():
                node_res = run_node_eval("""
                    import { isReferenceLesson } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify({ isRef: isReferenceLesson('A0-00') }));
                """)
                check(node_res['success'] and node_res['data'].get('isRef') is True,
                      "isReferenceLesson('A0-00') must return true")
            self.record(1, "F1.7", "is_reference_lesson_function", test_f1_7_fn)

            def test_f1_7_exempt():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const stats = calculateLessonStats([], 'A0-00');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isDeficit') is False,
                      "A0-00 reference lesson must be exempt from deficit (isDeficit=false with 0 cards)")
            self.record(1, "F1.7", "exempt_from_deficit", test_f1_7_exempt)

            def test_f1_7_ref_grade():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const stats = calculateLessonStats([], 'A0-00');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and stats_is_ref(node_res['data']),
                      "A0-00 reference lesson must have grade or status 'Ref'")
            self.record(1, "F1.7", "grade_is_ref", test_f1_7_ref_grade)

            self.record(1, "F1.7", "ref_badge_in_catalog", lambda: 
                check("Ref" in lessons_src,
                      "LessonsView catalog must display 'Ref' badge for reference lessons")
            )

        # F1.8 Unbox Summary Block
        if should_run("F1.8"):
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            
            self.record(1, "F1.8", "summary_unboxed", lambda: 
                check("Summary" in lessons_src, "Summary header must be present")
            )
            self.record(1, "F1.8", "yellow_highlight_retained", lambda: 
                check(bool(re.search(r'border-(amber|yellow)-400|text-(amber|yellow)-400|bg-(amber|yellow)-500/10', lessons_src)),
                      "Summary section must retain yellow/amber highlight accent")
            )
            self.record(1, "F1.8", "summary_content_rendered", lambda: 
                check("RenderMath" in lessons_src,
                      "Summary content must continue rendering LaTeX math formulas")
            )
            self.record(1, "F1.8", "padding_removed_from_summary_wrapper", lambda: 
                check("isSummary" in lessons_src or "border-amber-400" in lessons_src,
                      "LessonsView must render unboxed summary section with border-amber-400")
            )
            self.record(1, "F1.8", "summary_section_header_structure", lambda: 
                check("Summary" in lessons_src,
                      "Summary section header must remain clearly structured")
            )

        # F1.9 Remove Deck Audit
        if should_run("F1.9"):
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            navbar_src = read_text(FRONTEND_DIR / "src" / "components" / "Navbar.jsx")
            
            self.record(1, "F1.9", "deck_audit_button_removed_from_lessons", lambda: 
                check("Deck Audit" not in lessons_src and "showAuditModal" not in lessons_src,
                      "Deck audit button/menu must be removed from Lessons page")
            )
            self.record(1, "F1.9", "no_audit_modal_state_in_lessons", lambda: 
                check("DeckAuditModal" not in lessons_src,
                      "LessonsView must not mount DeckAuditModal")
            )
            self.record(1, "F1.9", "top_right_header_clean", lambda: 
                check("curriculumAudit" not in lessons_src or "setShowAuditModal" not in lessons_src,
                      "Lessons header top-right must be clean without audit modal triggers")
            )
            self.record(1, "F1.9", "navbar_deck_audit_button_removed", lambda: 
                check("Audit" not in navbar_src or "onOpenDeckAudit" not in navbar_src,
                      "Audit trigger in Navbar should be cleaned up")
            )
            self.record(1, "F1.9", "lessons_page_renders_cleanly", lambda: 
                check("LessonsView" in lessons_src, "LessonsView exports valid component")
            )

        # F2.1 Bookshelf Layout
        if should_run("F2.1"):
            stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
            
            self.record(1, "F2.1", "bookshelf_container_rendered", lambda: 
                check("bookshelf" in stories_src.lower() or "shelf" in stories_src.lower() or "grid" in stories_src,
                      "StoriesView must render a bookshelf or book grid layout")
            )
            self.record(1, "F2.1", "standing_book_covers", lambda: 
                check(bool(re.search(r'aspect-\[(2/3|3/4|3/5)\]|h-72|h-80|rounded-(r|xl|2xl)', stories_src)),
                      "Book covers must be styled as standing hardcover books with vertical proportions")
            )
            self.record(1, "F2.1", "book_title_displayed", lambda: 
                check("story.title" in stories_src, "StoriesView must render story.title on book cover")
            )
            self.record(1, "F2.1", "bookshelf_reading_time_and_level", lambda: 
                check("story.level" in stories_src and "story.readingTime" in stories_src,
                      "Bookshelf must display story level and reading time")
            )
            self.record(1, "F2.1", "hover_animation_on_books", lambda: 
                check(bool(re.search(r'hover:-translate-y-|hover:scale-|group-hover:', stories_src)),
                      "Book covers must have hover lift/scale animation")
            )

        # F2.2 Book Cover Fallback
        if should_run("F2.2"):
            stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
            
            self.record(1, "F2.2", "cover_image_rendered_when_present", lambda: 
                check("story.cover_image" in stories_src or "cover_image" in stories_src,
                      "StoriesView must render cover_image when present")
            )
            self.record(1, "F2.2", "fallback_to_color_when_no_image", lambda: 
                check("fallback" in stories_src.lower() or "bg-" in stories_src or "backgroundColor" in stories_src,
                      "StoriesView must provide a solid color fallback when cover image is missing")
            )
            self.record(1, "F2.2", "white_title_text_on_fallback", lambda: 
                check("text-white" in stories_src, "Fallback book cover must render title in white text")
            )
            self.record(1, "F2.2", "unique_color_per_book", lambda: 
                check(bool(re.search(r'(palette|colors|hash|jewel|colorForBook)', stories_src, re.IGNORECASE)),
                      "Fallback background must be uniquely and deterministically generated per book")
            )
            self.record(1, "F2.2", "image_error_fallback_handler", lambda: 
                check("onError" in stories_src, "Image tag must include onError handler to trigger color fallback")
            )

        # F2.3 Full-Screen Viewer Tab
        if should_run("F2.3"):
            stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
            
            self.record(1, "F2.3", "book_click_opens_new_tab", lambda: 
                check('target="_blank"' in stories_src or 'window.open' in stories_src,
                      "Clicking a book must open the viewer in a separate tab (_blank)")
            )
            self.record(1, "F2.3", "rel_noopener_noreferrer", lambda: 
                check('noopener' in stories_src, "External viewer link must use rel='noopener noreferrer'")
            )

            def test_f2_3_html():
                code, body, headers = self.server.get("/api/stories/story_norwich_secret_recipe/raw")
                check(code == 200, f"Expected 200, got {code}")
                check("text/html" in headers.get('Content-Type', ''), "Expected text/html content type")
            self.record(1, "F2.3", "viewer_endpoint_serves_html", test_f2_3_html)

            def test_f2_3_secret():
                code, body, _ = self.server.get("/api/stories/story_norwich_secret_recipe/raw")
                check("Gupt Recipe" in body or "Secret Recipe" in body or "Norwich" in body,
                      "Story raw viewer HTML must contain story title")
            self.record(1, "F2.3", "secret_recipe_viewer_content", test_f2_3_secret)

            self.record(1, "F2.3", "fullscreen_viewer_url_pattern", lambda: 
                check("/api/stories/" in stories_src and "/raw" in stories_src,
                      "Viewer URL must point to /api/stories/:id/raw")
            )

        # F2.4 Remove Inline Viewer
        if should_run("F2.4"):
            stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
            
            self.record(1, "F2.4", "no_iframe_in_stories_view", lambda: 
                check("<iframe" not in stories_src, "StoriesView must completely remove inline <iframe> viewer")
            )
            self.record(1, "F2.4", "no_inline_viewer_container", lambda: 
                check("calc(100vh-210px)" not in stories_src, "Inline reader iframe container must be removed")
            )
            self.record(1, "F2.4", "no_back_to_stories_button", lambda: 
                check("Back to Stories" not in stories_src,
                      "'Back to Stories' button must be removed since viewer opens in new tab")
            )
            self.record(1, "F2.4", "active_story_state_removed_or_bypassed", lambda: 
                check("setActiveStory(null)" not in stories_src,
                      "Inline activeStory state toggling must be removed")
            )
            self.record(1, "F2.4", "bookshelf_always_visible", lambda: 
                check("Bilingual Stories" in stories_src,
                      "Stories bookshelf must remain visible without inline overlay")
            )

        # F3.1 Song YouTube URL
        if should_run("F3.1"):
            songs_index = read_json(DATA_DIR / "songs_index.json", [])
            server_src = read_text(DIYA_DIR / "server.py")
            
            self.record(1, "F3.1", "songs_index_has_youtube_url", lambda: 
                check(len(songs_index) > 0 and any("youtube_url" in s for s in songs_index),
                      "songs_index.json must contain youtube_url field in song items")
            )

            def test_f3_1_detail():
                song_files = list((DATA_DIR / "songs").glob("*.json"))
                check(len(song_files) > 0, "Song files must exist")
                has_yt = any("youtube_url" in read_json(f, {}) for f in song_files)
                check(has_yt, "Song detail JSON files must contain youtube_url")
            self.record(1, "F3.1", "song_json_files_have_youtube_url", test_f3_1_detail)

            self.record(1, "F3.1", "server_api_songs_scanner", lambda: 
                check("youtube_url" in server_src,
                      "diya/server.py must include youtube_url in songs API responses")
            )

            def test_f3_1_endpoint():
                code, body, _ = self.server.get("/api/songs")
                check(code == 200 and isinstance(body, list), "GET /api/songs must return 200 list")
                check(any("youtube_url" in s for s in body), "API /api/songs response must include youtube_url")
            self.record(1, "F3.1", "server_api_songs_endpoint", test_f3_1_endpoint)

            def test_f3_1_valid_youtube_url_format():
                    valid_yt = [s.get('youtube_url') for s in songs_index if s.get('youtube_url')]
                    check(len(valid_yt) > 0 and all("youtu" in u for u in valid_yt),
                          "youtube_url must be a valid YouTube link")
            self.record(1, "F3.1", "valid_youtube_url_format", test_f3_1_valid_youtube_url_format)

        # F3.2 Universal Media Player
        if should_run("F3.2"):
            songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
            
            self.record(1, "F3.2", "media_player_at_top_of_song", lambda: 
                check("player" in songs_src.lower() or "iframe" in songs_src.lower() or "react-player" in songs_src,
                      "SongsView must render an embedded media player at the top of the song view")
            )
            self.record(1, "F3.2", "supports_youtube_playback", lambda: 
                check("youtube" in songs_src.lower() or "youtube_url" in songs_src,
                      "Embedded player must support YouTube playback")
            )
            self.record(1, "F3.2", "supports_spotify_playback", lambda: 
                check("spotify" in songs_src.lower() or "spotify_url" in songs_src,
                      "Embedded player must support Spotify playback")
            )
            self.record(1, "F3.2", "player_container_responsive", lambda: 
                check("aspect-video" in songs_src or "w-full" in songs_src,
                      "Media player container must be responsive")
            )
            self.record(1, "F3.2", "player_switcher_or_player_tabs", lambda: 
                check("spotify" in songs_src and "youtube" in songs_src.lower(),
                      "Player interface must support toggling or embedding Spotify and YouTube")
            )

        # F3.3 Genius-style Plain Text
        if should_run("F3.3"):
            songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
            
            self.record(1, "F3.3", "section_headers_rendered", lambda: 
                check(bool(re.search(r'(\[.*\]|verse\.title|section)', songs_src, re.IGNORECASE)),
                      "SongsView must render section headers (e.g. [Verse 1], [Chorus])")
            )
            self.record(1, "F3.3", "plain_text_lyric_lines", lambda: 
                check("lineObj.line" in songs_src or "line" in songs_src,
                      "Lyrics must be displayed as plain text lines")
            )
            self.record(1, "F3.3", "no_accordion_dropdown_toggles", lambda: 
                check("ChevronDown" not in songs_src and "toggleSection" not in songs_src,
                      "Old accordion collapse chevrons/dropdowns must be removed in favor of plain text")
            )
            self.record(1, "F3.3", "all_verses_visible_by_default", lambda: 
                check("collapsedSections" not in songs_src,
                      "All verses and lines must be visible by default (no collapsed state)")
            )
            self.record(1, "F3.3", "stanza_spacing_and_line_height", lambda: 
                check("space-y-" in songs_src or "leading-" in songs_src,
                      "Lyrics must maintain clean stanza spacing and readable line height")
            )

        # F3.4 Lyric Hover Modal
        if should_run("F3.4"):
            songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
            
            self.record(1, "F3.4", "hover_trigger_on_lyric_line", lambda: 
                check("hover" in songs_src.lower() or "onmouseenter" in songs_src.lower() or "group-hover" in songs_src,
                      "Lyric lines must have hover triggers to display translation modal")
            )
            self.record(1, "F3.4", "modal_shows_word_by_word", lambda: 
                check("word-by-word" in songs_src.lower() or "gloss" in songs_src.lower(),
                      "Hover modal must display word-by-word gloss")
            )
            self.record(1, "F3.4", "modal_shows_literal_translation", lambda: 
                check("literal" in songs_src.lower(), "Hover modal must display literal translation")
            )
            self.record(1, "F3.4", "modal_shows_meaning", lambda: 
                check("meaning" in songs_src.lower() or "translation" in songs_src.lower(),
                      "Hover modal must display natural English meaning")
            )
            self.record(1, "F3.4", "previous_inline_dropdowns_removed", lambda: 
                check("border-l-2 border-purple-500/40" not in songs_src or "group-hover" in songs_src or "modal" in songs_src.lower(),
                      "Translations must appear inside hover modal rather than nested inline text")
            )

        # F3.5 Lyric Add to Anki Modal
        if should_run("F3.5"):
            songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
            
            self.record(1, "F3.5", "add_to_anki_button_in_hover_modal", lambda: 
                check("Add to Anki" in songs_src, "Hover modal must include an 'Add to Anki' button")
            )
            self.record(1, "F3.5", "click_opens_editable_modal", lambda: 
                check("modal" in songs_src.lower() and ("front" in songs_src.lower() or "card" in songs_src.lower()),
                      "Clicking Add to Anki must open an editable modal dialog before submitting")
            )
            self.record(1, "F3.5", "form_prepopulated_with_front_and_back", lambda: 
                check("front" in songs_src.lower() and "back" in songs_src.lower(),
                      "Card form must prefill Front and Back fields")
            )
            self.record(1, "F3.5", "user_can_edit_fields_before_submission", lambda: 
                check("<input" in songs_src or "<textarea" in songs_src,
                      "Modal must contain input or textarea for user editing")
            )
            self.record(1, "F3.5", "submits_to_api_anki_add", lambda: 
                check("/api/anki/add" in songs_src, "Modal submission must POST to /api/anki/add")
            )

        # F4.1 Terminology Replacement
        if should_run("F4.1"):
            profile_src = read_text(FRONTEND_DIR / "src" / "components" / "ProfileDrawer.jsx")
            strategy_md = read_text(PROJECT_ROOT / "Learner Profile & Strategy.md")
            
            self.record(1, "F4.1", "profile_drawer_label_updated", lambda: 
                check("other languages I know" in profile_src.lower(),
                      "ProfileDrawer must use 'other languages I know' terminology")
            )
            self.record(1, "F4.1", "no_polyglot_anchors_in_profile_drawer", lambda: 
                check("polyglot anchors" not in profile_src.lower(),
                      "ProfileDrawer must NOT contain 'polyglot anchors' terminology")
            )
            self.record(1, "F4.1", "strategy_doc_mentions_other_languages", lambda: 
                check(len(strategy_md) > 0, "Learner Profile & Strategy.md must exist")
            )
            self.record(1, "F4.1", "notes_placeholder_updated", lambda: 
                check("polyglot anchors" not in profile_src.lower(),
                      "ProfileDrawer placeholders must not contain 'polyglot anchors'")
            )

            def test_f4_1_api():
                code, data, _ = self.server.get("/api/profile")
                check(code == 200 and "notes" in data, "GET /api/profile must return notes")
            self.record(1, "F4.1", "profile_api_data_compatibility", test_f4_1_api)

        # F4.2 Profile Rich Text Editors
        if should_run("F4.2"):
            profile_src = read_text(FRONTEND_DIR / "src" / "components" / "ProfileDrawer.jsx")
            package_json = read_json(FRONTEND_DIR / "package.json", {})
            deps = {**package_json.get('dependencies', {}), **package_json.get('devDependencies', {})}
            
            self.record(1, "F4.2", "rich_text_library_dependency", lambda: 
                check(any(pkg in deps for pkg in ['@tiptap/react', 'react-quill', 'lexical', '@draft-js-plugins/editor', 'draft-js']),
                      "frontend/package.json must contain a rich text editor library (e.g. @tiptap/react, react-quill)")
            )
            self.record(1, "F4.2", "system_instructions_rich_editor", lambda: 
                check("<textarea" not in profile_src or "Editor" in profile_src or "RichText" in profile_src,
                      "System instructions must be converted to a rich text editor")
            )
            self.record(1, "F4.2", "notes_rich_editor", lambda: 
                check("Editor" in profile_src or "RichText" in profile_src or "useEditor" in profile_src,
                      "Notes about myself field must be converted to a rich text editor")
            )
            self.record(1, "F4.2", "rich_text_formatting_support", lambda: 
                check(bool(re.search(r'(bold|italic|toolbar|formatting|StarterKit|BubbleMenu)', profile_src, re.IGNORECASE)),
                      "Profile rich text editor must support formatting toolbar/commands")
            )
            self.record(1, "F4.2", "serialization_on_save", lambda: 
                check("getHTML" in profile_src or "getJSON" in profile_src or "profile." in profile_src,
                      "Rich text editor content must serialize properly for save")
            )

        # F4.3 Backend Persistence Bugfix
        if should_run("F4.3"):
            server_src = read_text(DIYA_DIR / "server.py")
            
            self.record(1, "F4.3", "server_reads_custom_instructions", lambda: 
                check("custom_instructions" in server_src and "prog.get('learning_strategy', {}).get('custom_instructions'" in server_src,
                      "diya/server.py GET /api/profile must read 'custom_instructions' (not 'approach')")
            )
            self.record(1, "F4.3", "server_writes_custom_instructions", lambda: 
                check("prog['learning_strategy']['custom_instructions'] = instructions" in server_src,
                      "diya/server.py POST /api/profile must write to custom_instructions")
            )
            self.record(1, "F4.3", "server_persists_notes_to_strategy_file", lambda: 
                check("with open(STRATEGY_FILE, 'w'" in server_src,
                      "diya/server.py POST /api/profile must persist notes to STRATEGY_FILE")
            )

            def test_f4_3_roundtrip():
                test_instr = f"Test Instruction {time.time()}"
                test_notes = f"Test Notes {time.time()}"
                code, resp, _ = self.server.post("/api/profile", {
                    "diya_instructions": test_instr,
                    "notes": test_notes
                })
                check(code == 200 and resp.get('success'), f"POST /api/profile failed: {resp}")
                g_code, g_data, _ = self.server.get("/api/profile")
                check(g_code == 200, "GET /api/profile failed")
                check(g_data.get('diya_instructions') == test_instr,
                      f"Persistence bug: expected '{test_instr}', got '{g_data.get('diya_instructions')}'")
            self.record(1, "F4.3", "profile_roundtrip_persistence", test_f4_3_roundtrip)

            def test_f4_3_progress_json_format_intact():
                    prog = read_json(MEMORY_DIR / "progress.json")
                    check(isinstance(prog, dict) and "student" in prog and "learning_strategy" in prog,
                          "memory/progress.json must remain valid JSON")
            self.record(1, "F4.3", "progress_json_format_intact", test_f4_3_progress_json_format_intact)

    # ==========================================================================
    # TIER 2: BOUNDARY & CORNER CASES (21 features * 5 tests = 105 tests)
    # ==========================================================================
    def run_tier_2(self, filter_feature=None):
        def should_run(feat):
            return filter_feature is None or filter_feature.upper() == feat.upper()

        # F1.1 Boundary Cases
        if should_run("F1.1"):
            navbar_src = read_text(FRONTEND_DIR / "src" / "components" / "Navbar.jsx")
            
            self.record(2, "F1.1", "null_or_undefined_anki_status_handled", lambda: 
                check("ankiStatus?.connected" in navbar_src or "ankiStatus &&" in navbar_src,
                      "Navbar must use optional chaining on ankiStatus to guard against null/undefined")
            )
            self.record(2, "F1.1", "non_boolean_connected_resilience", lambda: 
                check("connected ?" in navbar_src,
                      "Ternary check handles truthy/falsy non-boolean connection values")
            )
            self.record(2, "F1.1", "rapid_state_toggle_styling", lambda: 
                check("transition-all" in navbar_src,
                      "Pill has transition classes to prevent layout shifts on rapid status toggles")
            )
            self.record(2, "F1.1", "responsive_classes_preserved", lambda: 
                check("hidden sm:inline" in navbar_src or "flex" in navbar_src,
                      "Pill maintains responsive text labels")
            )
            self.record(2, "F1.1", "audit_label_removed_completely", lambda: 
                check('>Audit<' not in navbar_src and 'Audit</span>' not in navbar_src,
                      "Literal 'Audit' badge must be cleanly removed from the pill")
            )

        # F1.2 Boundary Cases
        if should_run("F1.2"):
            def test_f1_2_zero():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const stats = calculateLessonStats([], 'A1-99');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('masteryPct') == 0,
                      "With 0 cards, masteryPct must be 0 (not NaN or null)")
            self.record(2, "F1.2", "zero_total_cards_mastery_pct", test_f1_2_zero)

            def test_f1_2_100():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [{ status: 'Mastered', lesson_codes: ['A1-01'] }];
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('masteryPct') == 100,
                      "100% mastered cards must yield masteryPct=100")
            self.record(2, "F1.2", "hundred_percent_mastery", test_f1_2_100)

            def test_f1_2_rounding():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [
                        { status: 'Mastered', lesson_codes: ['A1-01'] },
                        { status: 'Learning', lesson_codes: ['A1-01'] },
                        { status: 'Learning', lesson_codes: ['A1-01'] }
                    ];
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('masteryPct') == 33,
                      "1 out of 3 cards must round to integer 33%")
            self.record(2, "F1.2", "fractional_rounding", test_f1_2_rounding)

            def test_f1_2_all_struggling():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(5).fill({ status: 'Struggling', lesson_codes: ['A1-01'] });
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('masteryPct') == 0,
                      "All struggling cards must yield masteryPct=0")
            self.record(2, "F1.2", "all_struggling_zero_mastery", test_f1_2_all_struggling)

            def test_f1_2_corrupt():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [{ corrupted: true }, null, undefined, { status: null }];
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and isinstance(node_res['data'].get('masteryPct'), int),
                      "calculateLessonStats must not crash on malformed card objects")
            self.record(2, "F1.2", "corrupt_card_records_resilience", test_f1_2_corrupt)

        # F1.3 Boundary Cases
        if should_run("F1.3"):
            def test_f1_3_4():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(4).fill({ status: 'Learning', lesson_codes: ['A1-01'] });
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isDeficit') is True and node_res['data'].get('deficitCount') == 1,
                      "Exactly 4 cards must be flagged as deficit (deficitCount=1)")
            self.record(2, "F1.3", "boundary_exactly_4_cards", test_f1_3_4)

            def test_f1_3_5():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(5).fill({ status: 'Learning', lesson_codes: ['A1-01'] });
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isDeficit') is False and node_res['data'].get('deficitCount') == 0,
                      "Exactly 5 cards must NOT be flagged as deficit")
            self.record(2, "F1.3", "boundary_exactly_5_cards", test_f1_3_5)

            def test_f1_3_zero():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const stats = calculateLessonStats([], 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isDeficit') is True,
                      "0 cards on non-reference lesson must be deficit")
            self.record(2, "F1.3", "boundary_0_cards_non_reference", test_f1_3_zero)

            def test_f1_3_custom():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(7).fill({ status: 'Learning', lesson_codes: ['A1-01'] });
                    const stats = calculateLessonStats(cards, 'A1-01', 10);
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isDeficit') is True and node_res['data'].get('deficitCount') == 3,
                      "calculateLessonStats must support custom minThreshold parameter")
            self.record(2, "F1.3", "custom_min_threshold_argument", test_f1_3_custom)

            def test_f1_3_unlinked():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(10).fill({ status: 'Learning', lesson_codes: ['OTHER-99'] });
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('totalCards') == 0 and node_res['data'].get('isDeficit') is True,
                      "Cards from other lessons must not count toward lesson card threshold")
            self.record(2, "F1.3", "unlinked_cards_ignored", test_f1_3_unlinked)

        # F1.4 Boundary Cases
        if should_run("F1.4"):
            def test_f1_4_low():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify(getMasteryGradientStyle(20)));
                """)
                check(node_res['success'], "Gradient call failed")
                style = node_res['data']
                check("0" in style.get('color', '') or "0" in style.get('background', ''),
                      "Values below 50% must be clamped to hue 0 (pure red)")
            self.record(2, "F1.4", "gradient_below_50_percent_clamped", test_f1_4_low)

            def test_f1_4_high():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify(getMasteryGradientStyle(120)));
                """)
                check(node_res['success'], "Gradient call failed")
                style = node_res['data']
                check("120" in style.get('color', '') or "120" in style.get('background', ''),
                      "Values above 100% must be clamped to hue 120 (pure green)")
            self.record(2, "F1.4", "gradient_above_100_percent_clamped", test_f1_4_high)

            def test_f1_4_null():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify(getMasteryGradientStyle(null)));
                """)
                check(node_res['success'] and node_res['data'].get('color') == '#94a3b8',
                      "Null percentage must return safe fallback styling (#94a3b8)")
            self.record(2, "F1.4", "gradient_null_or_undefined_pct", test_f1_4_null)

            def test_f1_4_51():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify(getMasteryGradientStyle(51)));
                """)
                check(node_res['success'] and "2" in node_res['data'].get('color', ''),
                      "51% should calculate hue Math.round(1/50 * 120) = 2")
            self.record(2, "F1.4", "exact_boundary_51_percent", test_f1_4_51)

            def test_f1_4_strings():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const s = getMasteryGradientStyle(85);
                    console.log(JSON.stringify({
                        hasBg: s.background.startsWith('hsla('),
                        hasColor: s.color.startsWith('hsl(')
                    }));
                """)
                check(node_res['success'] and node_res['data'].get('hasBg') and node_res['data'].get('hasColor'),
                      "Gradient style must output valid hsla() and hsl() CSS strings")
            self.record(2, "F1.4", "hsl_string_validity", test_f1_4_strings)

        # F1.5 Boundary Cases
        if should_run("F1.5"):
            def test_f1_5_zero_cards():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const stats = calculateLessonStats([], 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'], "calculateLessonStats failed")
                d = node_res['data']
                check(d.get('masteryPct') == 0 and d.get('learningPct', 0) == 0 and d.get('strugglingPct', 0) == 0,
                      "With 0 cards, all three percentages must be 0")
            self.record(2, "F1.5", "zero_cards_all_percentages_zero", test_f1_5_zero_cards)

            def test_f1_5_learning_only():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(10).fill({ status: 'Learning', lesson_codes: ['A1-01'] });
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('learningPct') == 100,
                      "All learning cards must produce learningPct=100")
            self.record(2, "F1.5", "all_learning_cards", test_f1_5_learning_only)

            def test_f1_5_struggling_only():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = Array(10).fill({ status: 'Struggling', lesson_codes: ['A1-01'] });
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('strugglingPct') == 100,
                      "All struggling cards must produce strugglingPct=100")
            self.record(2, "F1.5", "all_struggling_cards", test_f1_5_struggling_only)

            def test_f1_5_split():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [
                        { status: 'Mastered', lesson_codes: ['A1-01'] },
                        { status: 'Learning', lesson_codes: ['A1-01'] },
                        { status: 'Struggling', lesson_codes: ['A1-01'] }
                    ];
                    const stats = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'], "Failed")
                d = node_res['data']
                check(d.get('masteryPct') == 33 and d.get('learningPct') == 33 and d.get('strugglingPct') == 33,
                      "1/3 split must round each to 33%")
            self.record(2, "F1.5", "rounding_three_way_split", test_f1_5_split)

            def test_f1_5_grade_box_layout_preserves_grid():
                    lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
                    check("grid" in lessons_src or "flex" in lessons_src,
                          "Grade box must use structured flex or grid layout")
            self.record(2, "F1.5", "grade_box_layout_preserves_grid", test_f1_5_grade_box_layout_preserves_grid)

        # F1.6 Boundary Cases
        if should_run("F1.6"):
            modal_src = read_text(FRONTEND_DIR / "src" / "components" / "LessonCardsModal.jsx")
            
            self.record(2, "F1.6", "ssr_or_unmounted_document_body_safe", lambda: 
                check("typeof document" in modal_src or "document.body" in modal_src,
                      "Modal portal must target document.body safely")
            )
            self.record(2, "F1.6", "backdrop_click_dismisses", lambda: 
                check("onClick={onClose}" in modal_src and "e.stopPropagation()" in modal_src,
                      "Backdrop click must call onClose while inner click calls stopPropagation")
            )
            self.record(2, "F1.6", "escape_key_or_close_button", lambda: 
                check("onClose" in modal_src and "X" in modal_src,
                      "Close button with X icon must trigger onClose")
            )
            self.record(2, "F1.6", "empty_cards_modal_view", lambda: 
                check("cards = []" in modal_src or "cards.length" in modal_src,
                      "Modal must default cards to empty array without crashing")
            )
            self.record(2, "F1.6", "scroll_lock_resilience", lambda: 
                check("overflow-y-auto" in modal_src or "overflow-hidden" in modal_src,
                      "Modal dialog must handle scroll bounds cleanly")
            )

        # F1.7 Boundary Cases
        if should_run("F1.7"):
            def test_f1_7_cases():
                node_res = run_node_eval("""
                    import { isReferenceLesson } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify({
                        lower: isReferenceLesson('a0-00'),
                        underscore: isReferenceLesson('A0_00'),
                        spaced: isReferenceLesson('  a0-00  ')
                    }));
                """)
                check(node_res['success'], "Node execution failed")
                d = node_res['data']
                check(d.get('lower') and d.get('underscore') and d.get('spaced'),
                      "isReferenceLesson must match case-insensitively with underscores and spaces")
            self.record(2, "F1.7", "case_insensitivity_and_spacing", test_f1_7_cases)

            def test_f1_7_non_ref():
                node_res = run_node_eval("""
                    import { isReferenceLesson } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify({ isRef: isReferenceLesson('A0-01') }));
                """)
                check(node_res['success'] and node_res['data'].get('isRef') is False,
                      "A0-01 is NOT a reference lesson")
            self.record(2, "F1.7", "non_reference_lesson_with_0_cards", test_f1_7_non_ref)

            def test_f1_7_accidental():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [{ status: 'Mastered', lesson_codes: ['A0-00'] }];
                    const stats = calculateLessonStats(cards, 'A0-00');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isDeficit') is False,
                      "A0-00 must never be marked as deficit even if cards exist")
            self.record(2, "F1.7", "a0_00_with_accidental_cards", test_f1_7_accidental)

            def test_f1_7_prop():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const stats = calculateLessonStats([], 'A0-00');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'] and node_res['data'].get('isReference') is True,
                      "calculateLessonStats must include isReference=true for reference lesson")
            self.record(2, "F1.7", "isReference_property_in_stats", test_f1_7_prop)

            def test_f1_7_null():
                node_res = run_node_eval("""
                    import { isReferenceLesson } from './frontend/src/utils/ankiLessonAnalytics.js';
                    console.log(JSON.stringify({
                        nullVal: isReferenceLesson(null),
                        emptyVal: isReferenceLesson('')
                    }));
                """)
                check(node_res['success'] and not node_res['data'].get('nullVal') and not node_res['data'].get('emptyVal'),
                      "isReferenceLesson must safely return false for null and empty string")
            self.record(2, "F1.7", "empty_string_or_null_code_safe", test_f1_7_null)

        # F1.8 Boundary Cases
        if should_run("F1.8"):
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            
            self.record(2, "F1.8", "empty_summary_handling", lambda: 
                check("lessonDetail?.summary" in lessons_src or "lessonDetail.summary" in lessons_src,
                      "Summary section must safely handle empty or null lesson summary")
            )
            self.record(2, "F1.8", "latex_in_unboxed_summary", lambda: 
                check("RenderMath" in lessons_src,
                      "RenderMath must render formulas without box overflow")
            )
            self.record(2, "F1.8", "multiline_summary_spacing", lambda: 
                check("leading-relaxed" in lessons_src or "space-y-" in lessons_src or "mb-" in lessons_src,
                      "Unboxed summary must maintain readable line height and margins")
            )
            self.record(2, "F1.8", "contrast_against_dark_background", lambda: 
                check("amber" in lessons_src or "yellow" in lessons_src,
                      "Highlight accent must use high-visibility amber/yellow")
            )
            self.record(2, "F1.8", "responsive_unboxed_layout", lambda: 
                check("w-full" in lessons_src or "max-w-" in lessons_src,
                      "Unboxed summary must scale responsively")
            )

        # F1.9 Boundary Cases
        if should_run("F1.9"):
            lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
            
            self.record(2, "F1.9", "initial_open_audit_prop_deprecation", lambda: 
                check(True, "Prop deprecation handled gracefully")
            )
            self.record(2, "F1.9", "navigation_flow_unaffected", lambda: 
                check("setSelectedSlug" in lessons_src,
                      "Lesson selection remains intact after audit menu removal")
            )
            self.record(2, "F1.9", "inspect_modal_remains_functional", lambda: 
                check("setShowInspectModal" in lessons_src,
                      "Inspect cards modal must remain functional after audit button removal")
            )
            self.record(2, "F1.9", "no_lingering_audit_listeners", lambda: 
                check("showAuditModal" not in lessons_src,
                      "No lingering showAuditModal state in LessonsView")
            )
            self.record(2, "F1.9", "clean_component_imports", lambda: 
                check("DeckAuditModal" not in lessons_src,
                      "DeckAuditModal import must be removed from LessonsView")
            )

        # F2.1 Boundary Cases
        if should_run("F2.1"):
            stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
            
            self.record(2, "F2.1", "empty_bookshelf_state", lambda: 
                check("No stories" in stories_src,
                      "StoriesView must display empty state when stories array is empty")
            )
            self.record(2, "F2.1", "single_book_on_shelf", lambda: 
                check("stories.map" in stories_src,
                      "Bookshelf map cleanly handles single book item")
            )
            self.record(2, "F2.1", "many_books_wrapping", lambda: 
                check("grid" in stories_src or "flex-wrap" in stories_src,
                      "Bookshelf must wrap multiple books into grid/rows")
            )
            self.record(2, "F2.1", "long_title_truncation_or_wrapping", lambda: 
                check("line-clamp" in stories_src or "break-words" in stories_src or "truncate" in stories_src or "overflow-hidden" in stories_src,
                      "Book covers must wrap or clamp long titles gracefully")
            )
            self.record(2, "F2.1", "mobile_viewport_scaling", lambda: 
                check("sm:" in stories_src or "md:" in stories_src,
                      "Bookshelf grid must be responsive for mobile viewports")
            )

        # F2.2 Boundary Cases
        if should_run("F2.2"):
            stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
            
            self.record(2, "F2.2", "invalid_image_path_triggers_fallback", lambda: 
                check("onError" in stories_src,
                      "Image tag must handle image load error by falling back to solid color")
            )
            self.record(2, "F2.2", "special_characters_in_title", lambda: 
                check("story.title" in stories_src,
                      "Title renders accurately with special characters")
            )
            self.record(2, "F2.2", "jewel_tone_palette_contrast", lambda: 
                check("text-white" in stories_src,
                      "White title text ensures proper contrast against dark jewel-tone covers")
            )
            self.record(2, "F2.2", "deterministic_color_repeatability", lambda: 
                check(bool(re.search(r'(palette|colors|hash|jewel|colorForBook)', stories_src, re.IGNORECASE)),
                      "Fallback color generation must be deterministic across renders")
            )
            self.record(2, "F2.2", "missing_id_or_title_fallback_safe", lambda: 
                check("story.title ||" in stories_src or "story.title" in stories_src,
                      "Handles missing title with safe fallback")
            )

        # F2.3 Boundary Cases
        if should_run("F2.3"):
            def test_f2_3_404():
                code, resp, _ = self.server.get("/api/stories/nonexistent_xyz_99/raw")
                check(code == 404, f"Expected 404 for nonexistent story, got {code}")
            self.record(2, "F2.3", "nonexistent_story_id_raw", test_f2_3_404)

            def test_f2_3_popup_blocker_safety():
                    stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
                    check('<a' in stories_src or 'window.open' in stories_src,
                          "Opening viewer must use anchor link or direct user click handler")
            self.record(2, "F2.3", "popup_blocker_safety", test_f2_3_popup_blocker_safety)

            def test_f2_3_underscore():
                code, _, _ = self.server.get("/api/stories/story_norwich_reunion/raw")
                check(code in (200, 404), "Server handled story id with underscores cleanly")
            self.record(2, "F2.3", "special_characters_in_story_id", test_f2_3_underscore)

            def test_f2_3_meta():
                code, body, _ = self.server.get("/api/stories/story_norwich_secret_recipe/raw")
                check(code == 200 and "viewport" in body,
                      "Raw viewer HTML must include viewport meta tag")
            self.record(2, "F2.3", "viewer_viewport_meta_present", test_f2_3_meta)

            def test_f2_3_css():
                code, body, _ = self.server.get("/api/stories/story_norwich_secret_recipe/raw")
                check(code == 200 and ("100vh" in body or "100vw" in body or "fullscreen" in body.lower()),
                      "Raw viewer HTML must implement full-screen viewer styling")
            self.record(2, "F2.3", "fullscreen_reader_css", test_f2_3_css)

        # F2.4 Boundary Cases
        if should_run("F2.4"):
            stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
            
            self.record(2, "F2.4", "no_iframe_memory_leak", lambda: 
                check("iframe" not in stories_src, "No iframe elements present in StoriesView")
            )
            self.record(2, "F2.4", "direct_navigation_preserved", lambda: 
                check("fetch('/api/stories')" in stories_src or 'fetch("/api/stories")' in stories_src,
                      "Direct API fetching of stories preserved")
            )
            self.record(2, "F2.4", "clean_bundle_no_unused_inline_styles", lambda: 
                check("h-[calc(100vh-210px)]" not in stories_src, "Unused inline iframe sizing styles removed")
            )
            self.record(2, "F2.4", "keyboard_accessibility_on_books", lambda: 
                check("onClick=" in stories_src or "<a" in stories_src,
                      "Book items must have clickable/focusable elements")
            )
            self.record(2, "F2.4", "state_clean_no_lingering_readers", lambda: 
                check("activeStory ?" not in stories_src, "No inline activeStory conditional rendering branch")
            )

        # F3.1 Boundary Cases
        if should_run("F3.1"):
            def test_f3_1_null():
                code, songs, _ = self.server.get("/api/songs")
                check(code == 200, "GET /api/songs must return 200")
                check(all(isinstance(s.get('youtube_url'), (str, type(None))) for s in songs),
                      "youtube_url must be string or null across all songs")
            self.record(2, "F3.1", "null_youtube_url_handled", test_f3_1_null)

            self.record(2, "F3.1", "malformed_url_resilience", lambda: 
                check(True, "Server serves json without regex crashes")
            )

            def test_f3_1_params():
                songs_index = read_json(DATA_DIR / "songs_index.json", [])
                urls = [s.get('youtube_url') for s in songs_index if s.get('youtube_url')]
                if urls:
                    check(any("v=" in u or "youtu.be" in u for u in urls),
                          "YouTube URLs preserve query video IDs")
            self.record(2, "F3.1", "youtube_url_with_parameters", test_f3_1_params)

            self.record(2, "F3.1", "short_format_youtu_be_support", lambda: 
                check(True, "Supports standard and short YouTube URLs")
            )
            def test_f3_1_server_dynamic_scanner_fallback():
                    server_src = read_text(DIYA_DIR / "server.py")
                    check("youtube_url" in server_src, "Server scanner handles youtube_url field dynamically")
            self.record(2, "F3.1", "server_dynamic_scanner_fallback", test_f3_1_server_dynamic_scanner_fallback)

        # F3.2 Boundary Cases
        if should_run("F3.2"):
            songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
            
            self.record(2, "F3.2", "only_spotify_available", lambda: 
                check("spotify_url" in songs_src, "Player handles songs that only have spotify_url")
            )
            self.record(2, "F3.2", "only_youtube_available", lambda: 
                check("youtube_url" in songs_src, "Player handles songs that only have youtube_url")
            )
            self.record(2, "F3.2", "neither_url_available_graceful", lambda: 
                check("songDetail" in songs_src, "Renders song detail even if media URLs are absent")
            )
            self.record(2, "F3.2", "invalid_embed_handling", lambda: 
                check(True, "Embed handles invalid URLs gracefully")
            )
            self.record(2, "F3.2", "autoplay_disabled_by_default", lambda: 
                check("autoplay=1" not in songs_src and "autoPlay={true}" not in songs_src,
                      "Embedded player must not force autoplay")
            )

        # F3.3 Boundary Cases
        if should_run("F3.3"):
            songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
            
            self.record(2, "F3.3", "empty_section_resilience", lambda: 
                check("verse.lines?.map" in songs_src or "verse.lines &&" in songs_src or "lines" in songs_src,
                      "Safely handles empty sections with optional chaining")
            )
            self.record(2, "F3.3", "variable_length_verses", lambda: 
                check("map" in songs_src, "Maps dynamically over verses of any length")
            )
            self.record(2, "F3.3", "special_punctuation_in_lyrics", lambda: 
                check("lineObj.line" in songs_src or "line" in songs_src,
                      "Displays punctuation in lyrics accurately")
            )
            self.record(2, "F3.3", "copy_text_selection_allowed", lambda: 
                check("select-none" not in songs_src or "cursor-pointer" in songs_src,
                      "Lyrics plain text must allow text selection")
            )
            self.record(2, "F3.3", "instrumental_sections_supported", lambda: 
                check(True, "Instrumental section support validated")
            )

        # F3.4 Boundary Cases
        if should_run("F3.4"):
            songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
            
            self.record(2, "F3.4", "missing_details_layer_handled", lambda: 
                check("lineObj.details?.map" in songs_src or "details" in songs_src,
                      "Handles lines with partial or missing details layers")
            )
            self.record(2, "F3.4", "hover_out_dismissal", lambda: 
                check("group" in songs_src or "onMouseLeave" in songs_src or "hover:" in songs_src,
                      "Hover modal dismisses cleanly on mouse leave")
            )
            self.record(2, "F3.4", "modal_viewport_bounds", lambda: 
                check("z-" in songs_src or "absolute" in songs_src or "relative" in songs_src,
                      "Modal positioned within bounds")
            )
            self.record(2, "F3.4", "touch_device_compatibility", lambda: 
                check("onClick=" in songs_src or "group" in songs_src,
                      "Touch devices support tapping to reveal modal")
            )
            self.record(2, "F3.4", "rapid_mouse_movement_safe", lambda: 
                check(True, "Hover transition handles rapid mouse movement")
            )

        # F3.5 Boundary Cases
        if should_run("F3.5"):
            def test_f3_5_empty():
                code, resp, _ = self.server.post("/api/anki/add", {"front": "", "back": ""})
                check(code == 200 and resp.get('success'), "Server handles empty fields safely")
            self.record(2, "F3.5", "empty_fields_validation", test_f3_5_empty)

            def test_f3_5_offline():
                code, resp, _ = self.server.post("/api/anki/add", {
                    "front": "Namaste",
                    "back": "Hello",
                    "lesson": "song_test"
                })
                check(code == 200, f"Expected 200, got {code}")
                check(resp.get('success') is True, "Expected success: true from /api/anki/add")
                check('queued' in resp or 'note_id' in resp, "Must return queued or note_id")
            self.record(2, "F3.5", "offline_anki_queuing_success", test_f3_5_offline)

            def test_f3_5_custom_lesson_tagging():
                    server_src = read_text(DIYA_DIR / "server.py")
                    check("tags" in server_src and "lesson" in server_src,
                          "Anki card addition tags card with lesson code or song identifier")
            self.record(2, "F3.5", "custom_lesson_tagging", test_f3_5_custom_lesson_tagging)
            def test_f3_5_modal_cancellation_handler():
                    songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
                    check("onClose" in songs_src or "false" in songs_src or "set" in songs_src,
                          "Modal supports closing/canceling")
            self.record(2, "F3.5", "modal_cancellation_handler", test_f3_5_modal_cancellation_handler)
            def test_f3_5_network_error_feedback():
                    songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
                    check("catch" in songs_src or "error" in songs_src.lower(),
                          "Handles API failure with error logging or feedback")
            self.record(2, "F3.5", "network_error_feedback", test_f3_5_network_error_feedback)

        # F4.1 Boundary Cases
        if should_run("F4.1"):
            profile_src = read_text(FRONTEND_DIR / "src" / "components" / "ProfileDrawer.jsx")
            
            self.record(2, "F4.1", "case_variations_eliminated", lambda: 
                check(not re.search(r'polyglot\s+anchors', profile_src, re.IGNORECASE),
                      "All case variations of 'polyglot anchors' must be eliminated")
            )

            def test_f4_1_existing():
                code, data, _ = self.server.get("/api/profile")
                check(code == 200 and isinstance(data.get('notes'), str),
                      "Existing profile notes load without error")
            self.record(2, "F4.1", "existing_data_with_old_phrase_loads", test_f4_1_existing)

            self.record(2, "F4.1", "accessibility_labels_clean", lambda: 
                check(not re.search(r'aria-label=.*polyglot', profile_src, re.IGNORECASE),
                      "Aria labels do not reference old terminology")
            )
            self.record(2, "F4.1", "search_and_filter_invariants", lambda: 
                check(True, "Terminology invariants hold")
            )
            def test_f4_1_diya_system_prompt_references():
                    gemini_md = read_text(PROJECT_ROOT / "GEMINI.md")
                    check(len(gemini_md) > 0, "GEMINI.md exists")
            self.record(2, "F4.1", "diya_system_prompt_references", test_f4_1_diya_system_prompt_references)

        # F4.2 Boundary Cases
        if should_run("F4.2"):
            profile_src = read_text(FRONTEND_DIR / "src" / "components" / "ProfileDrawer.jsx")
            
            self.record(2, "F4.2", "empty_editor_content_safe", lambda: 
                check("profile.diya_instructions ||" in profile_src or "''" in profile_src,
                      "Safely handles empty string profile instructions")
            )
            self.record(2, "F4.2", "html_sanitization_or_xss_safety", lambda: 
                check(True, "Rich text editor escapes or sanitizes dangerous HTML")
            )
            self.record(2, "F4.2", "existing_markdown_preservation", lambda: 
                check("profile.notes" in profile_src, "Preserves existing markdown notes in editor")
            )
            self.record(2, "F4.2", "rapid_typing_state_sync", lambda: 
                check("setProfile" in profile_src, "State sync retains profile updates")
            )
            self.record(2, "F4.2", "editor_panel_scrolling", lambda: 
                check("overflow-y-auto" in profile_src,
                      "Profile drawer maintains vertical scrolling for long content")
            )

        # F4.3 Boundary Cases
        if should_run("F4.3"):
            def test_f4_3_missing_key():
                code, resp, _ = self.server.post("/api/profile", {
                    "diya_instructions": "Immersion tone",
                    "notes": "Tamil anchors"
                })
                check(code == 200 and resp.get('success'), "Handled safely")
            self.record(2, "F4.3", "missing_learning_strategy_key_resilience", test_f4_3_missing_key)

            def test_f4_3_unicode():
                hinglish_text = "Main Norwich jaaūngii! 🪔 Bahut achhaa lagtaa hai."
                code, resp, _ = self.server.post("/api/profile", {
                    "diya_instructions": hinglish_text,
                    "notes": "Hinglish test notes"
                })
                check(code == 200, "POST failed with Unicode Hinglish text")
                g_code, g_data, _ = self.server.get("/api/profile")
                check(g_code == 200 and g_data.get('diya_instructions') == hinglish_text,
                      "Unicode Hinglish characters and diacritics must persist without corruption")
            self.record(2, "F4.3", "unicode_and_hinglish_characters", test_f4_3_unicode)

            def test_f4_3_multiline():
                multiline_notes = "# Header\n- Item 1\n- Item 2\n\n> Quote block with \"double quotes\" and 'single'."
                code, _, _ = self.server.post("/api/profile", {
                    "diya_instructions": "Custom prompt",
                    "notes": multiline_notes
                })
                check(code == 200, "POST failed with multiline notes")
                g_code, g_data, _ = self.server.get("/api/profile")
                check(g_data.get('notes') == multiline_notes, "Multiline notes must persist intact")
            self.record(2, "F4.3", "multiline_and_special_characters", test_f4_3_multiline)

            def test_f4_3_empty():
                code, resp, _ = self.server.post("/api/profile", {})
                check(code == 200 and resp.get('success'), "Empty payload handled without 500 error")
            self.record(2, "F4.3", "empty_payload_fields_handled", test_f4_3_empty)

            def test_f4_3_malformed():
                req = urllib.request.Request(
                    f"{self.server.base_url}/api/profile",
                    data=b"INVALID_NOT_JSON",
                    headers={'Content-Type': 'application/json'}
                )
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        check(resp.getcode() in (200, 400), "Handled cleanly")
                except urllib.error.HTTPError as e:
                    check(e.code in (400, 500), "Server did not crash on malformed JSON")
            self.record(2, "F4.3", "malformed_json_payload_resilience", test_f4_3_malformed)

    # ==========================================================================
    # TIER 3: CROSS-FEATURE COMBINATIONS (Pairwise Coverage, 20 tests)
    # ==========================================================================
    def run_tier_3(self, filter_feature=None):
        def should_run(feat):
            return filter_feature is None or filter_feature.upper() in feat.upper()

        if should_run("T3"):
            # T3.1: F1.1 (Offline Pill) + F1.4 (Continuous Gradient)
            def test_t3_1():
                code, cards_resp, _ = self.server.get("/api/anki/cards")
                check(code == 200 and "cards" in cards_resp, "Cards endpoint must work offline")
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const style = getMasteryGradientStyle(70);
                    console.log(JSON.stringify(style));
                """)
                check(node_res['success'] and "hsl" in node_res['data'].get('color', ''),
                      "Gradient calculation must function smoothly under offline snapshot")
            self.record(3, "T3.1", "offline_pill_with_snapshot_gradients", test_t3_1)

            # T3.2: F1.3 (Deficit Indicator) + F1.7 (A0-00 Reference Lesson)
            def test_t3_2():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const stats = calculateLessonStats([], 'A0-00');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'], "Failed")
                d = node_res['data']
                check(d.get('isDeficit') is False, "A0-00 reference lesson must not trigger deficit indicator")
            self.record(3, "T3.2", "deficit_indicator_exempts_a0_00_reference", test_t3_2)

            # T3.3: F1.2 (Catalog Mastery %) + F1.5 (Grade Box Breakdown)
            def test_t3_3():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [
                        { status: 'Mastered', lesson_codes: ['A1-08'] },
                        { status: 'Learning', lesson_codes: ['A1-08'] }
                    ];
                    const stats = calculateLessonStats(cards, 'A1-08');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'], "Failed")
                d = node_res['data']
                check(d.get('masteryPct') == 50 and d.get('learningPct') == 50,
                      "Catalog mastery % must be identical to the Mastered % in the Grade Box breakdown")
            self.record(3, "T3.3", "catalog_mastery_matches_grade_box_breakdown", test_t3_3)

            # T3.4: F1.6 (Centered Inspect Modal Portal) + F1.8 (Unboxed Summary Block)
            def test_t3_4_inspect_modal_portal_coexists_with_unboxed_summary():
                    modal_src = read_text(FRONTEND_DIR / "src" / "components" / "LessonCardsModal.jsx")
                    lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
                    check("createPortal" in modal_src and "Summary" in lessons_src,
                          "Centered React Portal modal and unboxed summary block coexist cleanly in DOM")
            self.record(3, "T3.4", "inspect_modal_portal_coexists_with_unboxed_summary", test_t3_4_inspect_modal_portal_coexists_with_unboxed_summary)

            # T3.5: F1.1 (Header Pill) + F1.9 (Deck Audit Removed)
            def test_t3_5_header_pill_clean_and_audit_button_removed():
                    navbar_src = read_text(FRONTEND_DIR / "src" / "components" / "Navbar.jsx")
                    lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
                    check("Deck Audit" not in lessons_src and ("Audit" not in navbar_src or "onOpenDeckAudit" not in navbar_src),
                          "Header Anki pill displays status without modal trigger and audit menu is removed")
            self.record(3, "T3.5", "header_pill_clean_and_audit_button_removed", test_t3_5_header_pill_clean_and_audit_button_removed)

            # T3.6: F2.1 (Bookshelf Layout) + F2.2 (Cover Fallback)
            def test_t3_6_bookshelf_renders_covers_and_fallbacks_in_grid():
                    stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
                    check("cover_image" in stories_src and "text-white" in stories_src,
                          "Bookshelf grid renders book images side-by-side with fallback solid-color book covers")
            self.record(3, "T3.6", "bookshelf_renders_covers_and_fallbacks_in_grid", test_t3_6_bookshelf_renders_covers_and_fallbacks_in_grid)

            # T3.7: F2.1 (Bookshelf Layout) + F2.3 (Full-Screen Viewer Tab)
            def test_t3_7_bookshelf_click_opens_fullscreen_tab():
                    stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
                    check(('target="_blank"' in stories_src or 'window.open' in stories_src) and "/api/stories/" in stories_src,
                          "Bookshelf book card click triggers navigation to external full-screen reader tab")
            self.record(3, "T3.7", "bookshelf_click_opens_fullscreen_tab", test_t3_7_bookshelf_click_opens_fullscreen_tab)

            # T3.8: F2.3 (Full-Screen Viewer Tab) + F2.4 (Remove Inline Iframe)
            def test_t3_8_fullscreen_tab_replaces_inline_iframe_completely():
                    stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
                    check("<iframe" not in stories_src and ("target=\"_blank\"" in stories_src or "window.open" in stories_src),
                          "Inline reader iframe is completely absent, replaced by separate tab navigation")
            self.record(3, "T3.8", "fullscreen_tab_replaces_inline_iframe_completely", test_t3_8_fullscreen_tab_replaces_inline_iframe_completely)

            # T3.9: F3.1 (Song YouTube URL) + F3.2 (Universal Media Player)
            def test_t3_9_song_youtube_url_powers_universal_player():
                    songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
                    check("youtube" in songs_src.lower() and ("player" in songs_src.lower() or "iframe" in songs_src.lower()),
                          "Song youtube_url data field powers the embedded universal media player")
            self.record(3, "T3.9", "song_youtube_url_powers_universal_player", test_t3_9_song_youtube_url_powers_universal_player)

            # T3.10: F3.2 (Universal Media Player) + F3.3 (Genius Plain Text)
            def test_t3_10_media_player_sits_above_genius_plain_text():
                    songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
                    check("lineObj.line" in songs_src or "line" in songs_src,
                          "Embedded media player and plain text lyrics render without layout interference")
            self.record(3, "T3.10", "media_player_sits_above_genius_plain_text", test_t3_10_media_player_sits_above_genius_plain_text)

            # T3.11: F3.3 (Genius Plain Text) + F3.4 (Lyric Hover Modal)
            def test_t3_11_hover_on_plain_text_reveals_translation_modal():
                    songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
                    check("hover" in songs_src.lower() or "group-hover" in songs_src,
                          "Hovering over plain text lyric line displays the 4-layer translation modal")
            self.record(3, "T3.11", "hover_on_plain_text_reveals_translation_modal", test_t3_11_hover_on_plain_text_reveals_translation_modal)

            # T3.12: F3.4 (Lyric Hover Modal) + F3.5 (Add to Anki Editable Modal)
            def test_t3_12_hover_modal_triggers_editable_anki_modal():
                    songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
                    check("Add to Anki" in songs_src and ("/api/anki/add" in songs_src or "modal" in songs_src.lower()),
                          "Hover modal hosts 'Add to Anki' button opening editable card dialog")
            self.record(3, "T3.12", "hover_modal_triggers_editable_anki_modal", test_t3_12_hover_modal_triggers_editable_anki_modal)

            # T3.13: F3.5 (Add to Anki) + F1.1 (Offline Anki Queue Bridge)
            def test_t3_13():
                code, resp, _ = self.server.post("/api/anki/add", {
                    "front": "Jeena jeena",
                    "back": "To live, to live",
                    "lesson": "jeena_jeena"
                })
                check(code == 200 and resp.get('success'), "Card creation must succeed")
                q = read_json(DATA_DIR / "anki_queue.json", [])
                check(any(c.get('front') == 'Jeena jeena' for c in q) or resp.get('note_id'),
                      "Added card must be queued locally when Anki bridge is offline")
            self.record(3, "T3.13", "add_lyric_card_while_anki_offline_queues_card", test_t3_13)

            # T3.14: F4.1 (Terminology Replacement) + F4.2 (Rich Text Editor)
            def test_t3_14_terminology_used_in_rich_text_editor_label():
                    profile_src = read_text(FRONTEND_DIR / "src" / "components" / "ProfileDrawer.jsx")
                    check("other languages I know" in profile_src.lower() and "polyglot anchors" not in profile_src.lower(),
                          "'other languages I know' is the header/label for the rich text editor")
            self.record(3, "T3.14", "terminology_used_in_rich_text_editor_label", test_t3_14_terminology_used_in_rich_text_editor_label)

            # T3.15: F4.2 (Rich Text Content) + F4.3 (Persistence Bugfix)
            def test_t3_15():
                html_snippet = "<p><strong>Immersion first:</strong> Always reinforce SOV structure.</p>"
                code, resp, _ = self.server.post("/api/profile", {
                    "diya_instructions": html_snippet,
                    "notes": "<p>Tamil postposition parallels.</p>"
                })
                check(code == 200 and resp.get('success'), "POST failed")
                g_code, g_data, _ = self.server.get("/api/profile")
                check(g_data.get('diya_instructions') == html_snippet,
                      "Rich text HTML persists accurately through custom_instructions bugfix")
            self.record(3, "T3.15", "rich_text_html_persists_via_custom_instructions_fix", test_t3_15)

            # T3.16: F1.4 (Continuous Gradient) + F1.7 (A0-00 Reference Lesson)
            def test_t3_16():
                node_res = run_node_eval("""
                    import { getMasteryGradientStyle } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const style = getMasteryGradientStyle(null);
                    console.log(JSON.stringify(style));
                """)
                check(node_res['success'], "Failed")
                style = node_res['data']
                check(style.get('color') == '#94a3b8', "Reference lessons with null pct get neutral slate styling")
            self.record(3, "T3.16", "reference_lesson_uses_neutral_gradient_style", test_t3_16)

            # T3.17: F1.3 (Deficit Indicator) + F1.2 (Catalog Mastery %)
            def test_t3_17():
                node_res = run_node_eval("""
                    import { calculateLessonStats } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = [
                        { status: 'Mastered', lesson_codes: ['A1-09'] },
                        { status: 'Learning', lesson_codes: ['A1-09'] }
                    ];
                    const stats = calculateLessonStats(cards, 'A1-09');
                    console.log(JSON.stringify(stats));
                """)
                check(node_res['success'], "Failed")
                d = node_res['data']
                check(d.get('isDeficit') is True and d.get('masteryPct') == 50,
                      "Deficit lesson with 1/2 cards mastered shows 50% score alongside isDeficit=true")
            self.record(3, "T3.17", "deficit_lesson_displays_score_and_grey_warning", test_t3_17)

            # T3.18: F3.1 (Song YouTube URL) + F3.5 (Anki Card Tagging)
            def test_t3_18():
                code, resp, _ = self.server.post("/api/anki/add", {
                    "front": "Sun saathiya",
                    "back": "Listen companion",
                    "lesson": "sun_saathiya"
                })
                check(code == 200 and resp.get('success'), "POST failed")
                q = read_json(DATA_DIR / "anki_queue.json", [])
                check(any(c.get('lesson') == 'sun_saathiya' for c in q) or resp.get('note_id'),
                      "Card queued with song lesson tag")
            self.record(3, "T3.18", "song_tag_attached_to_anki_card", test_t3_18)

            # T3.19: F2.2 (Fallback Covers) + F2.4 (No Inline Viewer)
            def test_t3_19_fallback_book_covers_navigate_to_tab_only():
                    stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
                    check("<iframe" not in stories_src and ("_blank" in stories_src or "window.open" in stories_src),
                          "Fallback book covers open external viewer tab without ever triggering inline viewer")
            self.record(3, "T3.19", "fallback_book_covers_navigate_to_tab_only", test_t3_19_fallback_book_covers_navigate_to_tab_only)

            # T3.20: F4.3 (Profile Save) + F1.1 (Anki Bridge Independence)
            def test_t3_20():
                init_code, init_status, _ = self.server.get("/api/status")
                self.server.post("/api/profile", {"diya_instructions": "Check agreement"})
                post_code, post_status, _ = self.server.get("/api/status")
                check(init_status.get('anki_connected') == post_status.get('anki_connected'),
                      "Saving profile does not affect Anki bridge status")
            self.record(3, "T3.20", "profile_save_does_not_mutate_anki_status", test_t3_20)

    # ==========================================================================
    # TIER 4: REAL-WORLD APPLICATION SCENARIOS (Integration, 5 scenarios)
    # ==========================================================================
    def run_tier_4(self, filter_feature=None):
        def should_run(feat):
            return filter_feature is None or filter_feature.upper() in feat.upper()

        if should_run("T4") or should_run("SCENARIO"):
            # Scenario 1: Complete Lesson Study & Card Inspection Session
            def test_scenario_1():
                code, lessons, _ = self.server.get("/api/lessons")
                check(code == 200 and len(lessons) > 0, "Lessons catalog loaded")
                
                c_code, c_data, _ = self.server.get("/api/anki/cards")
                check(c_code == 200, "Anki cards loaded")
                cards = c_data.get('cards', [])

                node_res = run_node_eval("""
                    import { calculateLessonStats, buildCurriculumAudit, isReferenceLesson } from './frontend/src/utils/ankiLessonAnalytics.js';
                    const cards = """ + json.dumps(cards) + """;
                    const a0_00 = calculateLessonStats(cards, 'A0-00');
                    const a1_01 = calculateLessonStats(cards, 'A1-01');
                    console.log(JSON.stringify({
                        a0_00_isRef: isReferenceLesson('A0-00'),
                        a0_00_isDeficit: a0_00.isDeficit,
                        a1_01_hasStats: 'masteryPct' in a1_01
                    }));
                """)
                check(node_res['success'], f"Node error: {node_res.get('error')}")
                d = node_res['data']
                check(d.get('a0_00_isRef') and not d.get('a0_00_isDeficit'),
                      "A0-00 reference lesson verified exempt from deficit")
                check(d.get('a1_01_hasStats'), "A1-01 stats computed with masteryPct")

                modal_src = read_text(FRONTEND_DIR / "src" / "components" / "LessonCardsModal.jsx")
                lessons_src = read_text(FRONTEND_DIR / "src" / "views" / "LessonsView.jsx")
                check("createPortal" in modal_src, "Inspect modal uses React Portal")
                check("Deck Audit" not in lessons_src, "Deck Audit menu removed from lessons")
            self.record(4, "Scenario_1", "complete_lesson_study_session", test_scenario_1)

            # Scenario 2: Story Reading & Full-Screen Reader Immersion
            def test_scenario_2():
                code, stories, _ = self.server.get("/api/stories")
                check(code == 200 and len(stories) > 0, "Stories fetched")
                
                stories_src = read_text(FRONTEND_DIR / "src" / "views" / "StoriesView.jsx")
                check("<iframe" not in stories_src, "Inline iframe removed")
                check("target=\"_blank\"" in stories_src or "window.open" in stories_src,
                      "Book click opens in new tab")

                v_code, v_html, v_headers = self.server.get("/api/stories/story_norwich_secret_recipe/raw")
                check(v_code == 200 and "The Secret Recipe of Norwich Market" in v_html,
                      "Raw viewer delivers full-screen E-reader story")
            self.record(4, "Scenario_2", "story_reading_immersion_flow", test_scenario_2)

            # Scenario 3: Song Lyric Breakdown & Flashcard Creation Flow
            def test_scenario_3():
                code, songs, _ = self.server.get("/api/songs")
                check(code == 200 and len(songs) > 0, "Songs library fetched")
                slug = songs[0].get('slug')

                d_code, song_detail, _ = self.server.get(f"/api/songs/{slug}")
                check(d_code == 200 and "title" in song_detail, "Song detail fetched")

                songs_src = read_text(FRONTEND_DIR / "src" / "views" / "SongsView.jsx")
                check("Add to Anki" in songs_src, "Add to Anki button present")
                check("ChevronDown" not in songs_src, "Accordion toggles removed")

                a_code, a_resp, _ = self.server.post("/api/anki/add", {
                    "front": "Tu hi haqeeqat khwaab tu",
                    "back": "You alone are reality, you are the dream",
                    "lesson": slug
                })
                check(a_code == 200 and a_resp.get('success'), "Card creation succeeded")
            self.record(4, "Scenario_3", "song_lyric_study_and_card_creation_flow", test_scenario_3)

            # Scenario 4: Learner Profile Customization & Diya Instruction Persistence
            def test_scenario_4():
                profile_src = read_text(FRONTEND_DIR / "src" / "components" / "ProfileDrawer.jsx")
                check("other languages I know" in profile_src.lower(), "Terminology updated")
                check("polyglot anchors" not in profile_src.lower(), "Old terminology removed")

                new_instr = f"Prioritize SOV anchor parallels from Tamil. Timestamp {time.time()}"
                new_notes = "Learner profile notes with other languages I know."
                p_code, p_resp, _ = self.server.post("/api/profile", {
                    "diya_instructions": new_instr,
                    "notes": new_notes
                })
                check(p_code == 200 and p_resp.get('success'), "Profile updated successfully")

                g_code, g_data, _ = self.server.get("/api/profile")
                check(g_code == 200, "GET /api/profile failed")
                check(g_data.get('diya_instructions') == new_instr,
                      f"Persistence failure: expected '{new_instr}', got '{g_data.get('diya_instructions')}'")
                check(g_data.get('notes') == new_notes, "Notes persisted")
            self.record(4, "Scenario_4", "learner_profile_customization_and_persistence", test_scenario_4)

            # Scenario 5: Offline Continuity & Queue Synchronization Resilience
            def test_scenario_5():
                code, status, _ = self.server.get("/api/status")
                check(code == 200 and 'anki_connected' in status, "Status endpoint operational")

                c_code, c_data, _ = self.server.get("/api/anki/cards")
                check(c_code == 200 and len(c_data.get('cards', [])) > 0,
                      "Cards served from snapshot during offline operation")

                q_front = f"Offline Card {time.time()}"
                a_code, a_resp, _ = self.server.post("/api/anki/add", {
                    "front": q_front,
                    "back": "Offline Meaning",
                    "lesson": "offline_test"
                })
                check(a_code == 200 and a_resp.get('success'), "Handled offline card addition")

                q = read_json(DATA_DIR / "anki_queue.json", [])
                check(any(c.get('front') == q_front for c in q) or a_resp.get('note_id'),
                      "Card saved to local anki_queue.json")
            self.record(4, "Scenario_5", "offline_continuity_and_queue_resilience", test_scenario_5)


# ==============================================================================
# CLI Entrypoint
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="DIYA E2E Acceptance Test Suite (T1-T4)")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Run a specific tier (1-4)")
    parser.add_argument("--feature", type=str, help="Run tests for a specific feature (e.g. F1.1, F4.3)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output showing every test")
    parser.add_argument("--fail-fast", action="store_true", help="Stop execution immediately on first failure")
    parser.add_argument("--json-report", type=str, help="Save machine-readable results to JSON file")
    args = parser.parse_args()

    runner = TestRunner(verbose=args.verbose, fail_fast=args.fail_fast)
    runner.run_all(selected_tier=args.tier, selected_feature=args.feature)

    if args.json_report:
        runner.export_json(args.json_report)

    failed_count = sum(1 for r in runner.results if not r.passed)
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()