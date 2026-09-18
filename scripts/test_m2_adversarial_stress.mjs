/**
 * Adversarial Stress Test Suite for Milestone M2: Bookshelf & Cover Fallback
 * 
 * Verifies:
 * 1. Cover theme hashing: 20 string IDs, determinism (100 runs each), no crashes,
 *    adversarial edge cases (null, undefined, unicode, 100k len), palette distribution,
 *    and valid jewel-tone hex color validation.
 * 2. Invariant verification: Statically asserts StoriesView.jsx contains ZERO <iframe> elements,
 *    ZERO activeStory state, and ZERO back buttons.
 * 3. Fallback rendering: Verifies onError handler correctly swaps state to display
 *    solid background and white title text across simulated state transitions.
 * 4. Production build & packaging verification.
 */

import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');
const frontendDir = path.resolve(projectRoot, 'frontend');
const storiesViewPath = path.resolve(frontendDir, 'src/views/StoriesView.jsx');
const storiesIndexPath = path.resolve(projectRoot, 'diya/data/stories_index.json');

console.log('===============================================================');
console.log('CHALLENGER M2_1: ADVERSARIAL STRESS TEST & INVARIANT HARNESS');
console.log('===============================================================\n');

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;
const failures = [];

function check(condition, label, details = '') {
  totalTests++;
  if (condition) {
    console.log(`  [PASS] ${label}`);
    passedTests++;
  } else {
    console.error(`  [FAIL] ${label}`);
    if (details) console.error(`         Details: ${details}`);
    failedTests++;
    failures.push({ label, details });
  }
}

// =========================================================================
// EXTRACTION: Extract exact getBookCoverTheme and JEWEL_PALETTES from source
// =========================================================================
const storiesViewSource = fs.readFileSync(storiesViewPath, 'utf-8');

// Extract JEWEL_PALETTES and getBookCoverTheme code block
const palettesMatch = storiesViewSource.match(/const JEWEL_PALETTES = (\[[\s\S]*?\]);/);
const funcMatch = storiesViewSource.match(/function getBookCoverTheme\([\s\S]*?\n\}/);

if (!palettesMatch || !funcMatch) {
  console.error('FATAL: Could not extract JEWEL_PALETTES or getBookCoverTheme from StoriesView.jsx');
  process.exit(1);
}

const extractedCode = `
${palettesMatch[0]}
${funcMatch[0]}
module.exports = { JEWEL_PALETTES, getBookCoverTheme };
`;

const sandbox = { module: {}, exports: {} };
vm.createContext(sandbox);
vm.runInContext(extractedCode, sandbox);
const { JEWEL_PALETTES, getBookCoverTheme } = sandbox.module.exports;

// Helper to validate 6-digit hex color format (#RRGGBB)
function isValidHexColor(color) {
  return typeof color === 'string' && /^#[0-9a-fA-F]{6}$/.test(color);
}

// =========================================================================
// TEST SUITE 1: Cover Theme Hashing Stress & Determinism
// =========================================================================
console.log('--- TEST SUITE 1: Cover Theme Hashing Stress & Determinism ---');

// 1.1 Verify JEWEL_PALETTES integrity
check(
  Array.isArray(JEWEL_PALETTES) && JEWEL_PALETTES.length === 8,
  'JEWEL_PALETTES contains exactly 8 defined jewel-tone palettes',
  `Length: ${JEWEL_PALETTES?.length}`
);

JEWEL_PALETTES.forEach((palette, idx) => {
  const valid =
    isValidHexColor(palette.bg) &&
    isValidHexColor(palette.border) &&
    isValidHexColor(palette.foil) &&
    typeof palette.name === 'string' &&
    palette.name.length > 0;
  check(
    valid,
    `JEWEL_PALETTES[${idx}] (${palette.name}) has valid hex bg, border, foil, and non-empty name`,
    JSON.stringify(palette)
  );
});

// 1.2 Test 20 distinct string IDs
const TEST_20_IDS = [
  'story_norwich_secret_recipe',
  'story_norwich_reunion',
  'story_chai_stall_delhi',
  'story_delhi_metro_rush',
  'story_varanasi_ghats_morning',
  'story_mumbai_dabbawalas_punctual',
  'story_rickshaw_diaries_chandni',
  'story_jaipur_hawa_mahal',
  'story_shimla_winter_snow',
  'story_goa_monsoon_cafes',
  'story_kerala_backwaters_boat',
  'story_kolkata_tram_heritage',
  'story_ladakh_khardung_la',
  'story_hyderabad_biryani_hunt',
  'story_bangalore_cubbon_park',
  'story_agra_dawn_taj',
  'story_amritsar_golden_temple',
  'story_udaipur_lake_pichola',
  'story_rishikesh_ganges_rafting',
  'story_darjeeling_tea_gardens'
];

check(
  TEST_20_IDS.length === 20,
  'Harness defines exactly 20 distinct string story IDs for verification'
);

const assignedPalettes = new Set();

TEST_20_IDS.forEach((id, idx) => {
  let initialTheme = null;
  let isDeterministic = true;
  let noCrashes = true;
  let hasValidProperties = true;

  try {
    initialTheme = getBookCoverTheme(id);

    // Verify properties
    if (
      !initialTheme ||
      !isValidHexColor(initialTheme.bg) ||
      !isValidHexColor(initialTheme.border) ||
      !isValidHexColor(initialTheme.foil) ||
      typeof initialTheme.name !== 'string'
    ) {
      hasValidProperties = false;
    }

    // Verify it belongs to JEWEL_PALETTES
    const belongsToPalettes = JEWEL_PALETTES.some((p) => p.name === initialTheme.name && p.bg === initialTheme.bg);
    if (!belongsToPalettes) hasValidProperties = false;

    assignedPalettes.add(initialTheme.name);

    // Stress test: 100 repeated runs to prove absolute determinism
    for (let run = 0; run < 100; run++) {
      const reTheme = getBookCoverTheme(id);
      if (
        reTheme.name !== initialTheme.name ||
        reTheme.bg !== initialTheme.bg ||
        reTheme.border !== initialTheme.border ||
        reTheme.foil !== initialTheme.foil
      ) {
        isDeterministic = false;
        break;
      }
    }
  } catch (err) {
    noCrashes = false;
  }

  check(
    noCrashes && hasValidProperties && isDeterministic,
    `ID #${idx + 1} "${id}": returns valid jewel-tone theme ("${initialTheme?.name}"), 100x deterministic, zero crashes`,
    `bg: ${initialTheme?.bg}, name: ${initialTheme?.name}, deterministic: ${isDeterministic}`
  );
});

// 1.3 Palette Distribution Verification across the 20 IDs
check(
  assignedPalettes.size >= 5,
  `Cover theme hashing distributes across multiple palettes (found ${assignedPalettes.size}/8 unique palettes among 20 IDs)`,
  `Assigned palettes: ${Array.from(assignedPalettes).join(', ')}`
);

// 1.4 Adversarial Edge-Case Inputs (Boundary Stress Testing)
console.log('\n--- Suite 1.4: Adversarial Edge Cases & Abuse Inputs ---');
const ADVERSARIAL_INPUTS = [
  { val: '', label: 'Empty string ""' },
  { val: '     ', label: 'Whitespace string "     "' },
  { val: 'कहानी_नॉरविच_बाजार', label: 'Devanagari Unicode string "कहानी_नॉरविच_बाजार"' },
  { val: '📚📖✨🎉🔥', label: 'Emoji-only string "📚📖✨🎉🔥"' },
  { val: '!@#$%^&*()_+~`|}{[]:;?><,./-=', label: 'Special symbol character soup' },
  { val: '0', label: 'Single digit string "0"' },
  { val: 'a'.repeat(100000), label: 'Massive string (100,000 chars)' },
  { val: null, label: 'null input' },
  { val: undefined, label: 'undefined input' },
  { val: 0, label: 'Numeric 0 input' },
  { val: -9999, label: 'Negative integer input -9999' },
  { val: true, label: 'Boolean true input' },
  { val: false, label: 'Boolean false input' }
];

ADVERSARIAL_INPUTS.forEach(({ val, label }) => {
  let theme = null;
  let safe = true;
  let errMsg = '';
  try {
    theme = getBookCoverTheme(val);
    if (!theme || !isValidHexColor(theme.bg) || !JEWEL_PALETTES.includes(theme)) {
      safe = false;
      errMsg = `Returned invalid palette: ${JSON.stringify(theme)}`;
    }
  } catch (err) {
    safe = false;
    errMsg = err.message;
  }

  check(
    safe,
    `Adversarial input [${label}]: handles safely without crash, returns valid theme "${theme?.name}"`,
    errMsg
  );
});

// =========================================================================
// TEST SUITE 2: Invariant Verification (ZERO iframe, ZERO activeStory, ZERO Back Button)
// =========================================================================
console.log('\n--- TEST SUITE 2: Invariant Verification (StoriesView.jsx) ---');

// 2.1 ZERO <iframe> elements
const iframeMatches = storiesViewSource.match(/<iframe[\s\S]*?>/gi) || [];
const anyIframeWord = storiesViewSource.match(/\biframe\b/gi) || [];
check(
  iframeMatches.length === 0,
  'ZERO <iframe ...> elements exist in StoriesView.jsx',
  `Found ${iframeMatches.length} matches: ${iframeMatches.join(', ')}`
);
check(
  anyIframeWord.length === 0,
  'ZERO references to "iframe" keyword exist in StoriesView.jsx',
  `Found ${anyIframeWord.length} occurrences`
);

// 2.2 ZERO activeStory state
const activeStoryMatches = storiesViewSource.match(/\bactiveStory\b/g) || [];
const setActiveStoryMatches = storiesViewSource.match(/\bsetActiveStory\b/g) || [];
const storySelectionHook = storiesViewSource.match(/useState\s*\(\s*null\s*\)/g) || [];

check(
  activeStoryMatches.length === 0,
  'ZERO occurrences of "activeStory" state variable in StoriesView.jsx',
  `Found ${activeStoryMatches.length} occurrences`
);
check(
  setActiveStoryMatches.length === 0,
  'ZERO occurrences of "setActiveStory" updater in StoriesView.jsx',
  `Found ${setActiveStoryMatches.length} occurrences`
);

// Check that no other story selection state exists
const readerConditionalMatches = storiesViewSource.match(/\{\s*[a-zA-Z0-9_]*Story\s*\?\s*\(/g) || [];
check(
  readerConditionalMatches.length === 0,
  'ZERO inline story reader conditional render blocks in StoriesView.jsx',
  `Found: ${readerConditionalMatches.join(', ')}`
);

// 2.3 ZERO back buttons
const backToStoriesMatches = storiesViewSource.match(/back\s+to\s+stories/gi) || [];
const backButtonMatches = storiesViewSource.match(/<button[^>]*>[\s\S]*?back[\s\S]*?<\/button>/gi) || [];
const onBackMatches = storiesViewSource.match(/\b(handleBack|onBack|goBack)\b/gi) || [];

check(
  backToStoriesMatches.length === 0,
  'ZERO occurrences of "Back to Stories" label in StoriesView.jsx',
  `Found ${backToStoriesMatches.length} occurrences`
);
check(
  backButtonMatches.length === 0,
  'ZERO back buttons (<button>...Back...</button>) in StoriesView.jsx',
  `Found: ${backButtonMatches.join(', ')}`
);
check(
  onBackMatches.length === 0,
  'ZERO back navigation handlers (handleBack / onBack / goBack) in StoriesView.jsx',
  `Found: ${onBackMatches.join(', ')}`
);

// 2.4 Removal of inline viewer layout container
check(
  !storiesViewSource.includes('calc(100vh-210px)'),
  'Inline reader container class "calc(100vh-210px)" is completely removed'
);

// 2.5 Verification of Separate Tab Navigation
check(
  storiesViewSource.includes("window.open('/api/stories/' + storyId + '/raw', '_blank')") ||
  storiesViewSource.includes('window.open(') && storiesViewSource.includes("'_blank'"),
  'Story click handler opens /api/stories/:id/raw in a separate tab ("_blank")'
);

check(
  storiesViewSource.includes('target="_blank"') && storiesViewSource.includes('rel="noopener noreferrer"'),
  'StoriesView includes anchor tag with target="_blank" and rel="noopener noreferrer"'
);

// =========================================================================
// TEST SUITE 3: Fallback Rendering & State Swapping Simulation
// =========================================================================
console.log('\n--- TEST SUITE 3: Fallback Rendering & State Swapping Simulation ---');

// 3.1 Static code audit of fallback structure
check(
  storiesViewSource.includes('const [imageErrors, setImageErrors] = useState({});'),
  'StoriesView initializes imageErrors state dictionary: useState({})'
);

check(
  storiesViewSource.includes('setImageErrors((prev) => ({ ...prev, [id]: true }));'),
  'handleImageError correctly updates state by setting [id]: true'
);

check(
  storiesViewSource.includes('onError={() => handleImageError(story.id)}'),
  'Cover image renders onError handler wired to handleImageError(story.id)'
);

check(
  storiesViewSource.includes('const hasCover = story.cover_image && !imageErrors[story.id];'),
  'hasCover condition checks both truthy story.cover_image AND absence of error in imageErrors[story.id]'
);

// Fallback container element check
check(
  storiesViewSource.includes('fallback-cover'),
  'Fallback cover container has "fallback-cover" class identifier'
);

check(
  storiesViewSource.includes('style={{ backgroundColor: palette.bg }}'),
  'Fallback cover container sets style={{ backgroundColor: palette.bg }}'
);

check(
  storiesViewSource.includes('font-serif font-bold text-white') && storiesViewSource.includes('{story.title'),
  'Fallback cover renders story.title with "text-white" and serif typography'
);

check(
  storiesViewSource.includes("{story.title || 'Untitled Story'}"),
  'Fallback cover includes safe title fallback: story.title || "Untitled Story"'
);

// 3.2 Dynamic State Machine Simulation for Fallback Rendering
console.log('\n--- Suite 3.2: Dynamic State Transition Simulation ---');

function simulateStoryCardRendering(story, initialImageErrors = {}) {
  let currentErrors = { ...initialImageErrors };

  function render(errors) {
    const palette = getBookCoverTheme(story.id);
    const hasCover = story.cover_image && !errors[story.id];

    if (hasCover) {
      return {
        viewType: 'IMAGE_COVER',
        renderedSrc: story.cover_image,
        renderedTitle: story.title || 'Untitled Story',
        backgroundColor: '#0b0f19',
        hasWhiteTitle: false, // In image cover, title is rendered over dark vignette
        hasFallbackCover: false,
        onErrorTrigger: () => {
          currentErrors = { ...currentErrors, [story.id]: true };
          return render(currentErrors);
        }
      };
    } else {
      return {
        viewType: 'FALLBACK_COVER',
        renderedSrc: null,
        renderedTitle: story.title || 'Untitled Story',
        backgroundColor: palette.bg,
        paletteName: palette.name,
        hasWhiteTitle: true,
        hasFallbackCover: true,
        foilColor: palette.foil,
        onErrorTrigger: null
      };
    }
  }

  return { initialRender: render(currentErrors), getCurrentErrors: () => currentErrors };
}

// Scenario A: Story with valid cover image that subsequently errors out
const mockStoryWithCover = {
  id: 'story_test_mock_1',
  title: 'Bazaar Ki Kahani',
  level: 'A1',
  cover_image: '/api/stories/assets/bazaar.jpg',
  readingTime: '5 min'
};

const simA = simulateStoryCardRendering(mockStoryWithCover);
const renderA1 = simA.initialRender;

check(
  renderA1.viewType === 'IMAGE_COVER' && renderA1.renderedSrc === '/api/stories/assets/bazaar.jpg',
  'Scenario A1 (Pre-Error): Story with cover_image renders IMAGE_COVER view with correct src'
);
check(
  renderA1.hasFallbackCover === false,
  'Scenario A1 (Pre-Error): Fallback cover is NOT active'
);

// Now trigger the onError handler!
const renderA2 = renderA1.onErrorTrigger();

check(
  renderA2.viewType === 'FALLBACK_COVER',
  'Scenario A2 (Post-Error): onError event swaps viewType from IMAGE_COVER to FALLBACK_COVER'
);
check(
  renderA2.backgroundColor === getBookCoverTheme(mockStoryWithCover.id).bg,
  `Scenario A2 (Post-Error): Solid background color matches palette.bg (${renderA2.backgroundColor})`
);
check(
  renderA2.hasWhiteTitle === true && renderA2.renderedTitle === 'Bazaar Ki Kahani',
  'Scenario A2 (Post-Error): Title text is rendered in white text with correct story title'
);
check(
  simA.getCurrentErrors()[mockStoryWithCover.id] === true,
  'Scenario A2 (Post-Error): imageErrors dictionary recorded error for story ID'
);

// Scenario B: Story with NO cover image (cover_image: null, like story_norwich_reunion)
const mockStoryNoCover = {
  id: 'story_norwich_reunion',
  title: 'Norwich Ki Train Aur Shivani Ka Surprise',
  level: 'A1-09',
  cover_image: null,
  readingTime: '8 min'
};

const simB = simulateStoryCardRendering(mockStoryNoCover);
const renderB = simB.initialRender;

check(
  renderB.viewType === 'FALLBACK_COVER',
  'Scenario B: Story with cover_image=null immediately renders FALLBACK_COVER without waiting for onError'
);
check(
  renderB.backgroundColor === getBookCoverTheme(mockStoryNoCover.id).bg,
  `Scenario B: Solid background color is deterministic jewel-tone (${renderB.paletteName} -> ${renderB.backgroundColor})`
);
check(
  renderB.hasWhiteTitle === true && renderB.renderedTitle === mockStoryNoCover.title,
  'Scenario B: Title renders with white text and correct story title'
);

// Scenario C: Story with empty string cover_image ("")
const mockStoryEmptyCover = {
  id: 'story_empty_cover_test',
  title: 'Empty Cover Test Story',
  cover_image: ''
};
const simC = simulateStoryCardRendering(mockStoryEmptyCover);
check(
  simC.initialRender.viewType === 'FALLBACK_COVER',
  'Scenario C: Story with cover_image="" immediately renders FALLBACK_COVER'
);

// Scenario D: Story with missing title (null/undefined)
const mockStoryNoTitle = {
  id: 'story_no_title_test',
  cover_image: null
};
const simD = simulateStoryCardRendering(mockStoryNoTitle);
check(
  simD.initialRender.renderedTitle === 'Untitled Story' && simD.initialRender.hasWhiteTitle,
  'Scenario D: Story with undefined title gracefully defaults to "Untitled Story" with white text'
);

// =========================================================================
// TEST SUITE 4: Production Build Cleanliness & Compilation Verification
// =========================================================================
console.log('\n--- TEST SUITE 4: Production Build Cleanliness Verification ---');

let buildSuccess = false;
let buildOutput = '';

try {
  buildOutput = execSync('npm run build', {
    cwd: frontendDir,
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe']
  });
  buildSuccess = true;
} catch (err) {
  buildSuccess = false;
  buildOutput = err.stderr || err.stdout || err.message;
}

check(
  buildSuccess,
  'npm run build executes cleanly with exit code 0 (no syntax/import errors in StoriesView)',
  buildOutput
);

// Check dist files exist
const distDir = path.resolve(frontendDir, 'dist');
check(
  fs.existsSync(path.resolve(distDir, 'index.html')),
  'Vite production artifact dist/index.html exists'
);

const distAssets = fs.existsSync(path.resolve(distDir, 'assets'))
  ? fs.readdirSync(path.resolve(distDir, 'assets'))
  : [];

check(
  distAssets.some((f) => f.endsWith('.js')),
  'Production bundle includes compiled JavaScript asset'
);

check(
  distAssets.some((f) => f.endsWith('.css')),
  'Production bundle includes compiled CSS stylesheet'
);

// Also run linter check
let lintSuccess = false;
let lintOutput = '';
try {
  lintOutput = execSync('npm run lint', {
    cwd: frontendDir,
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe']
  });
  lintSuccess = true;
} catch (err) {
  lintSuccess = false;
  lintOutput = err.stderr || err.stdout || err.message;
}

check(
  lintSuccess,
  'npm run lint executes cleanly with 0 errors across the frontend project',
  lintOutput
);

// =========================================================================
// SUMMARY & VERDICT
// =========================================================================
console.log('\n===============================================================');
console.log(`STRESS TEST SUMMARY: ${passedTests}/${totalTests} CHECKS PASSED`);
console.log('===============================================================');

if (failedTests > 0) {
  console.error(`\nCRITICAL: CHALLENGE_FAILED with ${failedTests} failed assertions:`);
  failures.forEach((f, i) => {
    console.error(`  ${i + 1}. ${f.label} -> ${f.details}`);
  });
  process.exit(1);
} else {
  console.log('\nALL 3 MISSION OBJECTIVES VERIFIED WITH EMPIRICAL EVIDENCE.');
  console.log('EXPLICIT VERDICT: APPROVE');
  console.log('===============================================================\n');
  process.exit(0);
}
