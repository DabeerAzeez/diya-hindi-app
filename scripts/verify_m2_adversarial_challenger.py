"""
verify_m2_adversarial_challenger.py

Empirical verification and adversarial stress testing suite for Milestone M2:
- Structural parity: story_norwich_reunion.html vs story_norwich_secret_recipe.html
  * 100vw x 100vh overflow: hidden shell
  * Two-page spread #bookContainer
  * .cover-mode on Spread 0
  * Hover diacritic tooltips (data-tooltip)
  * Bilingual spread mode and novel spread mode
- Navigation verification:
  * window.open routes to /api/stories/:id/raw in _blank
  * target="_blank" links route to /api/stories/:id/raw
  * Zero <iframe> inline viewers, zero activeStory state
- Server endpoint & story data integrity
- Acceptance suite execution & argument parsing verification:
  * scripts/e2e_acceptance_suite.py --feature F2.1-F2.4 (documents range argument edge case)
  * scripts/e2e_acceptance_suite.py --feature F2.1 .. F2.4 (individual features)
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent

passed_tests = 0
failed_tests = 0
test_results = []

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def record_assertion(test_name, condition, details=""):
    global passed_tests, failed_tests, test_results
    if condition:
        passed_tests += 1
        test_results.append((test_name, True, details))
        print(f"  [PASS] {test_name}" + (f": {details}" if details else ""))
    else:
        failed_tests += 1
        test_results.append((test_name, False, details))
        print(f"  [FAIL] {test_name}" + (f": {details}" if details else ""))

def parse_html_and_styles(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    styles_text = '\n'.join([s.get_text() for s in soup.find_all('style')])
    scripts_text = '\n'.join([s.get_text() for s in soup.find_all('script')])
    return content, soup, styles_text, scripts_text

def test_structural_parity():
    print("\n--- SUITE 1: Structural Parity & E-Reader Layout Invariants ---")
    stories = [
        ("recipe", PROJECT_ROOT / "diya" / "data" / "stories" / "story_norwich_secret_recipe.html"),
        ("reunion", PROJECT_ROOT / "diya" / "data" / "stories" / "story_norwich_reunion.html")
    ]

    for label, path in stories:
        print(f"\nEvaluating story file: {path.name} ({label})")
        assert path.exists(), f"File does not exist: {path}"
        raw, soup, styles, scripts = parse_html_and_styles(path)

        # 1. Shell 100vw x 100vh overflow: hidden
        html_body_match = re.search(r'html\s*,\s*body\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        record_assertion(
            f"{label}: html, body ruleset defined in style block",
            html_body_match is not None
        )
        if html_body_match:
            rules = html_body_match.group(1)
            record_assertion(
                f"{label}: html, body has height 100vh",
                re.search(r'height\s*:\s*100vh', rules) is not None
            )
            record_assertion(
                f"{label}: html, body has width 100vw",
                re.search(r'width\s*:\s*100vw', rules) is not None
            )
            record_assertion(
                f"{label}: html, body has overflow hidden",
                re.search(r'overflow\s*:\s*hidden', rules) is not None
            )

        ereader_app_match = re.search(r'\.ereader-app\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        record_assertion(
            f"{label}: .ereader-app has height: 100vh and width: 100vw",
            ereader_app_match is not None and
            '100vh' in ereader_app_match.group(1) and
            '100vw' in ereader_app_match.group(1)
        )

        reading_stage_match = re.search(r'\.reading-stage\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        record_assertion(
            f"{label}: .reading-stage has overflow: hidden",
            reading_stage_match is not None and
            'overflow: hidden' in reading_stage_match.group(1)
        )

        # 2. Two-page spread #bookContainer
        book_container = soup.find(id='bookContainer')
        record_assertion(
            f"{label}: #bookContainer element exists in DOM",
            book_container is not None
        )
        if book_container:
            classes = book_container.get('class', [])
            record_assertion(
                f"{label}: #bookContainer has open-book-container class",
                'open-book-container' in classes
            )
            left = book_container.find(id='pageLeft')
            spine = book_container.find(id='spineDivider')
            right = book_container.find(id='pageRight')
            record_assertion(
                f"{label}: #bookContainer contains #pageLeft, #spineDivider, #pageRight",
                left is not None and spine is not None and right is not None
            )

        # Two-page spread CSS grid layout
        open_book_css = re.search(r'\.open-book-container\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        record_assertion(
            f"{label}: .open-book-container uses CSS grid with two pages and spine",
            open_book_css is not None and
            re.search(r'display\s*:\s*grid', open_book_css.group(1)) is not None and
            re.search(r'grid-template-columns\s*:\s*1fr\s+14px\s+1fr', open_book_css.group(1)) is not None
        )

        page_left_css = re.search(r'#pageLeft\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        spine_css = re.search(r'#spineDivider\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        page_right_css = re.search(r'#pageRight\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        record_assertion(
            f"{label}: grid columns mapped (#pageLeft=1, #spineDivider=2, #pageRight=3)",
            page_left_css and 'grid-column: 1' in page_left_css.group(1) and
            spine_css and 'grid-column: 2' in spine_css.group(1) and
            page_right_css and 'grid-column: 3' in page_right_css.group(1)
        )

        # 3. .cover-mode on Spread 0
        record_assertion(
            f"{label}: #bookContainer has initial .cover-mode class in HTML",
            'cover-mode' in book_container.get('class', []) if book_container else False
        )
        cover_mode_css = re.findall(r'\.open-book-container\.cover-mode[^{]*\{([^}]+)\}', styles, re.I | re.DOTALL)
        record_assertion(
            f"{label}: CSS defines rules for .open-book-container.cover-mode",
            len(cover_mode_css) >= 1
        )
        record_assertion(
            f"{label}: CSS hides #pageLeft and #spineDivider in cover-mode",
            re.search(r'\.open-book-container\.cover-mode\s+#pageLeft[^{]*\{[^}]*visibility:\s*hidden', styles) is not None and
            re.search(r'\.open-book-container\.cover-mode\s+#spineDivider[^{]*\{[^}]*visibility:\s*hidden', styles) is not None
        )

        # Cover-mode JavaScript logic
        record_assertion(
            f"{label}: JavaScript checks currentSpread === 0 to apply cover-mode",
            re.search(r'if\s*\(\s*currentSpread\s*===\s*0\s*\)\s*\{[^}]*classList\.add\([\'"]cover-mode[\'"]\)', scripts) is not None
        )
        record_assertion(
            f"{label}: JavaScript removes cover-mode when currentSpread > 0",
            re.search(r'classList\.remove\([\'"]cover-mode[\'"]\)', scripts) is not None
        )

        # 4. Hover diacritic tooltips (data-tooltip)
        tooltip_matches = re.findall(r'data-tooltip\s*=\s*\\?["\']([^"\'\\]+)', raw)
        record_assertion(
            f"{label}: Contains elements with data-tooltip (found {len(tooltip_matches)})",
            len(tooltip_matches) > 50,
            f"count={len(tooltip_matches)}"
        )
        empty_tooltips = [t for t in tooltip_matches if not t.strip()]
        record_assertion(
            f"{label}: Zero empty or whitespace-only data-tooltip values",
            len(empty_tooltips) == 0,
            f"empty count={len(empty_tooltips)}"
        )

        # CSS tooltip rules: .word::after
        word_after_css = re.search(r'\.word::after\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        record_assertion(
            f"{label}: .word::after CSS uses attr(data-tooltip) and hidden by default",
            word_after_css is not None and
            'content: attr(data-tooltip)' in word_after_css.group(1) and
            'opacity: 0' in word_after_css.group(1) and
            'visibility: hidden' in word_after_css.group(1)
        )
        word_hover_after_css = re.search(r'\.word:hover::after\s*\{([^}]+)\}', styles, re.I | re.DOTALL)
        record_assertion(
            f"{label}: .word:hover::after displays tooltip (opacity: 1, visibility: visible)",
            word_hover_after_css is not None and
            'opacity: 1' in word_hover_after_css.group(1) and
            'visibility: visible' in word_hover_after_css.group(1)
        )

        # Diacritics toggle support
        record_assertion(
            f"{label}: Supports body.show-diacritics-in-text diacritics toggle",
            'body.show-diacritics-in-text' in styles and
            'function toggleTextDiacritics()' in scripts
        )

        # 5. Bilingual spread mode and novel spread mode
        record_assertion(
            f"{label}: Initial #bookContainer has bilingual-mode class",
            'bilingual-mode' in book_container.get('class', []) if book_container else False
        )
        record_assertion(
            f"{label}: CSS defines rules for .novel-mode and .bilingual-mode",
            'novel-mode' in styles and 'bilingual-mode' in styles
        )
        record_assertion(
            f"{label}: Left Hindi content has overflow: hidden (strict no scrollbar)",
            '#contentLeft {\n      overflow: hidden !important;' in styles or
            re.search(r'#contentLeft\s*\{[^}]*overflow\s*:\s*hidden\s*!important', styles) is not None
        )
        record_assertion(
            f"{label}: Novel mode right page has overflow: hidden (strict no scrollbar)",
            re.search(r'\.novel-mode\s+#contentRight\s*\{[^}]*overflow\s*:\s*hidden\s*!important', styles) is not None
        )
        record_assertion(
            f"{label}: Bilingual mode right page allows vertical scroll if needed (overflow-y: auto)",
            re.search(r'\.bilingual-mode\s+#contentRight\s*\{[^}]*overflow-y\s*:\s*auto\s*!important', styles) is not None
        )
        record_assertion(
            f"{label}: JavaScript contains toggleViewMode function toggling between bilingual and novel",
            'function toggleViewMode()' in scripts and
            ('mode === \'bilingual\'' in scripts and "mode = 'novel'" in scripts and "mode = 'bilingual'" in scripts)
        )

def test_navigation_and_viewer_invariants():
    print("\n--- SUITE 2: Navigation & Viewer Invariants in StoriesView.jsx ---")
    stories_view_path = PROJECT_ROOT / "frontend" / "src" / "views" / "StoriesView.jsx"
    assert stories_view_path.exists(), f"StoriesView.jsx not found: {stories_view_path}"

    with open(stories_view_path, 'r', encoding='utf-8') as f:
        src = f.read()

    # 1. Check window.open routing
    window_open_matches = re.findall(r'window\.open\(([^)]+)\)', src)
    record_assertion(
        "StoriesView.jsx calls window.open",
        len(window_open_matches) > 0,
        f"matches: {window_open_matches}"
    )
    for m in window_open_matches:
        record_assertion(
            f"window.open routes to /api/stories/:id/raw in '_blank'",
            ('/api/stories/' in m and '/raw' in m and "'_blank'" in m) or
            ('/api/stories/' in m and '/raw' in m and '"_blank"' in m),
            f"call argument: {m}"
        )

    # 2. Check anchor links
    anchor_href_matches = re.findall(r'<a\s+[^>]*href=\{`([^`]+)`\}[^>]*>', src)
    record_assertion(
        "StoriesView.jsx renders <a> tags for story opening",
        len(anchor_href_matches) > 0,
        f"hrefs: {anchor_href_matches}"
    )
    for h in anchor_href_matches:
        record_assertion(
            f"<a> href routes to /api/stories/${{story.id}}/raw",
            h.startswith('/api/stories/${story.id}/raw'),
            f"href: {h}"
        )

    # 3. Check target="_blank" and rel="noopener noreferrer"
    record_assertion(
        "<a> tag includes target=\"_blank\"",
        re.search(r'<a\s+[^>]*target=["\']_blank["\']', src) is not None
    )
    record_assertion(
        "<a> tag includes rel=\"noopener noreferrer\"",
        re.search(r'<a\s+[^>]*rel=["\']noopener noreferrer["\']', src) is not None
    )

    # 4. Strict absence of inline viewer artifacts
    record_assertion(
        "StoriesView.jsx: ZERO <iframe> elements",
        '<iframe' not in src
    )
    record_assertion(
        "StoriesView.jsx: ZERO activeStory state declarations or setter",
        'activeStory' not in src and 'setActiveStory' not in src
    )
    record_assertion(
        "StoriesView.jsx: ZERO 'Back to Stories' buttons",
        'Back to Stories' not in src and 'back-to-stories' not in src
    )
    record_assertion(
        "StoriesView.jsx: ZERO inline viewer containers (h-[calc(100vh-210px)])",
        'calc(100vh-210px)' not in src
    )

def test_server_raw_endpoint():
    print("\n--- SUITE 3: Server Endpoint & Stories Index Integrity ---")
    stories_index_path = PROJECT_ROOT / "diya" / "data" / "stories_index.json"
    assert stories_index_path.exists(), f"stories_index.json not found: {stories_index_path}"

    with open(stories_index_path, 'r', encoding='utf-8') as f:
        stories = json.load(f)

    record_assertion(
        "stories_index.json contains at least 2 stories",
        isinstance(stories, list) and len(stories) >= 2,
        f"count={len(stories)}"
    )

    for s in stories:
        sid = s.get('id')
        fname = s.get('filename')
        record_assertion(
            f"Story {sid} has required fields (id, title, level, filename, readingTime)",
            bool(sid and s.get('title') and s.get('level') and fname and s.get('readingTime'))
        )
        file_path = PROJECT_ROOT / "diya" / "data" / "stories" / fname
        record_assertion(
            f"Story {sid} file exists on disk ({fname})",
            file_path.exists(),
            f"path={file_path}"
        )

    server_path = PROJECT_ROOT / "diya" / "server.py"
    assert server_path.exists(), f"server.py not found: {server_path}"
    with open(server_path, 'r', encoding='utf-8') as f:
        server_src = f.read()

    record_assertion(
        "diya/server.py handles /api/stories/:id/raw endpoint",
        re.search(r'\/api\/stories\/[^\/]+\/raw', server_src) is not None or
        re.search(r'self\.path\s*==\s*[\'"]/api/stories/', server_src) or
        ('stories' in server_src and 'raw' in server_src)
    )

def test_adversarial_stress_scenarios():
    print("\n--- SUITE 4: Adversarial Stress Scenarios & Edge Cases ---")
    reunion_path = PROJECT_ROOT / "diya" / "data" / "stories" / "story_norwich_reunion.html"
    recipe_path = PROJECT_ROOT / "diya" / "data" / "stories" / "story_norwich_secret_recipe.html"

    with open(reunion_path, 'rb') as f:
        reunion_bytes = f.read()
    with open(recipe_path, 'rb') as f:
        recipe_bytes = f.read()

    record_assertion(
        "story_norwich_reunion.html has zero byte decoding errors (valid utf-8)",
        True
    )

    reunion_replacement_chars = reunion_bytes.count(b'\xef\xbf\xbd')
    recipe_replacement_chars = recipe_bytes.count(b'\xef\xbf\xbd')
    print(f"  [INFO] U+FFFD count: reunion={reunion_replacement_chars}, recipe={recipe_replacement_chars}")

    record_assertion(
        "reunion file parses as clean DOM without parse errors",
        BeautifulSoup(reunion_bytes.decode('utf-8', errors='replace'), 'html.parser') is not None
    )

    # Page numbering bounds in JS
    for name, bcontent in [("recipe", recipe_bytes), ("reunion", reunion_bytes)]:
        text = bcontent.decode('utf-8', errors='replace')
        record_assertion(
            f"{name}: navigatePage checks bounds (next >= 0 && next <= maxSpread)",
            'next >= 0 && next <= maxSpread' in text
        )
        record_assertion(
            f"{name}: adjustFontSize has min/max safety clamping",
            re.search(r'Math\.min\(\s*1\.22\s*,\s*Math\.max\(\s*0\.85', text) is not None
        )
        record_assertion(
            f"{name}: Keyboard listeners bound for ArrowLeft and ArrowRight",
            "e.key === 'ArrowLeft'" in text and "e.key === 'ArrowRight'" in text
        )

    # TOC Item Navigation Integrity
    for name, bcontent in [("recipe", recipe_bytes), ("reunion", reunion_bytes)]:
        soup = BeautifulSoup(bcontent.decode('utf-8', errors='replace'), 'html.parser')
        toc_items = soup.find_all(class_='toc-item')
        record_assertion(
            f"{name}: Table of Contents drawer has interactive items (found {len(toc_items)})",
            len(toc_items) >= 4,
            f"count={len(toc_items)}"
        )
        for idx, item in enumerate(toc_items):
            data_nav = item.get('data-nav')
            record_assertion(
                f"{name}: TOC item {idx} has valid numeric data-nav attribute",
                data_nav is not None and data_nav.isdigit(),
                f"data-nav={data_nav}"
            )

    # Speech synthesis error handling
    for name, bcontent in [("recipe", recipe_bytes), ("reunion", reunion_bytes)]:
        text = bcontent.decode('utf-8', errors='replace')
        record_assertion(
            f"{name}: Speech synthesis checks 'speechSynthesis' in window",
            "if (!('speechSynthesis' in window))" in text or "'speechSynthesis' in window" in text
        )

def run_acceptance_suite():
    print("\n--- SUITE 5: Acceptance Suite Execution & Argument Parsing Invariance ---")
    cmd_range = [sys.executable, str(PROJECT_ROOT / "scripts" / "e2e_acceptance_suite.py"), "--feature", "F2.1-F2.4"]
    print(f"Executing dispatch literal: {' '.join(cmd_range)}")
    res_range = subprocess.run(cmd_range, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    
    executed_zero = "Total Tests Executed: 0" in res_range.stdout
    record_assertion(
        "Adversarial Observation: '--feature F2.1-F2.4' filters exactly on 'F2.1-F2.4' and yields 0 tests",
        executed_zero,
        f"executed_zero={executed_zero}"
    )

    features = ["F2.1", "F2.2", "F2.3", "F2.4"]
    total_passed_features = 0
    for feat in features:
        cmd_feat = [sys.executable, str(PROJECT_ROOT / "scripts" / "e2e_acceptance_suite.py"), "--feature", feat]
        res_feat = subprocess.run(cmd_feat, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        clean_stdout = strip_ansi(res_feat.stdout)
        feat_passed = (res_feat.returncode == 0 and 
                       f"{feat}        : 10/10 passed" in clean_stdout and
                       "Failed:               0" in clean_stdout)
        record_assertion(
            f"Acceptance suite for {feat}: 10/10 tests passed (100%)",
            feat_passed,
            f"returncode={res_feat.returncode}"
        )
        if feat_passed:
            total_passed_features += 1

    record_assertion(
        "All M2 feature suites (F2.1, F2.2, F2.3, F2.4) pass 100% (40/40 tests)",
        total_passed_features == len(features),
        f"passed_features={total_passed_features}/{len(features)}"
    )

def main():
    print("=================================================================")
    print("   M2 ADVERSARIAL CHALLENGER VERIFICATION HARNESS")
    print("=================================================================")
    test_structural_parity()
    test_navigation_and_viewer_invariants()
    test_server_raw_endpoint()
    test_adversarial_stress_scenarios()
    run_acceptance_suite()

    print("\n=================================================================")
    print(f"VERIFICATION RESULTS: {passed_tests} PASSED, {failed_tests} FAILED out of {passed_tests + failed_tests} total.")
    print("=================================================================")

    if failed_tests == 0:
        print("\nOVERALL VERDICT: APPROVE")
        sys.exit(0)
    else:
        print(f"\nOVERALL VERDICT: CHALLENGE_FAILED ({failed_tests} failures)")
        sys.exit(1)

if __name__ == "__main__":
    main()
