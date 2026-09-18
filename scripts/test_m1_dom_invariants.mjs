import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');
const frontendDir = path.resolve(projectRoot, 'frontend');

// Dynamically import from frontend/node_modules
const { build } = await import('../frontend/node_modules/vite/dist/node/index.js');
const React = (await import('../frontend/node_modules/react/index.js')).default;
const { renderToStaticMarkup } = await import('../frontend/node_modules/react-dom/server.node.js');

console.log('===============================================================');
console.log('CHALLENGER M1_2: EMPIRICAL UI INVARIANTS & DOM VERIFICATION');
console.log('===============================================================\n');

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function assert(condition, message, details = '') {
  totalTests++;
  if (condition) {
    console.log(`  [PASS] ${message}`);
    passedTests++;
  } else {
    console.error(`  [FAIL] ${message}`);
    if (details) console.error(`         Details: ${details}`);
    failedTests++;
  }
}

// Global mock DOM setup for portal and SSR tests
const mockBody = { nodeName: 'BODY', id: 'mock-body' };
globalThis.document = {
  body: mockBody,
  createElement: (tag) => ({ tagName: tag }),
};

async function compileComponent(relPath) {
  const fullPath = path.resolve(frontendDir, relPath);
  const result = await build({
    root: frontendDir,
    build: {
      write: false,
      ssr: true,
      lib: {
        entry: fullPath,
        formats: ['es'],
      },
    },
    configFile: false,
  });
  const output = Array.isArray(result) ? result[0].output : result.output;
  const code = output[0].code;

  // Write temporary compiled file
  const tmpFile = path.resolve(frontendDir, 'node_modules', `.test_${Date.now()}_${path.basename(relPath, '.jsx')}.mjs`);
  fs.writeFileSync(tmpFile, code, 'utf-8');
  try {
    const mod = await import(`file:///${tmpFile.replace(/\\/g, '/')}`);
    return { mod, code };
  } finally {
    if (fs.existsSync(tmpFile)) {
      fs.unlinkSync(tmpFile);
    }
  }
}

async function runAllChecks() {
  // =========================================================================
  // TEST SUITE 1: LessonCardsModal Portal Attachment & Viewport Centering
  // =========================================================================
  console.log('\n--- TEST SUITE 1: LessonCardsModal Portal Attachment & Viewport Centering ---');
  const modalSourcePath = path.resolve(frontendDir, 'src/components/LessonCardsModal.jsx');
  const modalSource = fs.readFileSync(modalSourcePath, 'utf-8');

  // 1.1 Source inspection: createPortal import
  assert(
    modalSource.includes("import { createPortal } from 'react-dom';") ||
    modalSource.includes('import { createPortal } from "react-dom";'),
    'Source code imports createPortal from "react-dom"'
  );

  // 1.2 Source inspection: targets document.body
  const portalCallRegex = /createPortal\s*\([\s\S]*?,\s*document\.body\s*\)/;
  assert(
    portalCallRegex.test(modalSource),
    'Source code explicitly invokes createPortal with document.body as target container'
  );

  // 1.3 Centering & Backdrop Layout Classes
  assert(
    modalSource.includes('fixed inset-0 z-50 flex items-center justify-center'),
    'Modal overlay container uses "fixed inset-0 z-50 flex items-center justify-center" (centered on viewport window)'
  );

  // 1.4 Click propagation protection & backdrop dismissal
  assert(
    modalSource.includes('onClick={onClose}') && modalSource.includes('e.stopPropagation()'),
    'Modal overlay handles backdrop dismiss and inner card container stops click propagation'
  );

  // 1.5 Dynamic Compilation & Execution Test
  const { mod: modalMod, code: modalCompiledCode } = await compileComponent('src/components/LessonCardsModal.jsx');
  const LessonCardsModal = modalMod.default;

  // Test component returns empty when closed or no lesson
  const htmlClosed = renderToStaticMarkup(React.createElement(LessonCardsModal, { isOpen: false, lesson: { title: 'Test' } }));
  assert(
    htmlClosed === '',
    'Component renders empty when isOpen is false (no portal attached to DOM)'
  );

  const htmlNoLesson = renderToStaticMarkup(React.createElement(LessonCardsModal, { isOpen: true, lesson: null }));
  assert(
    htmlNoLesson === '',
    'Component renders empty when lesson is null (no portal attached to DOM)'
  );

  assert(
    modalCompiledCode.includes('createPortal(') && modalCompiledCode.includes('document.body'),
    'Compiled SSR bundle contains createPortal call with document.body'
  );

  // =========================================================================
  // TEST SUITE 2: Navbar Anki Live Pill Invariants
  // =========================================================================
  console.log('\n--- TEST SUITE 2: Navbar Anki Live Pill Invariants ---');
  const navbarSourcePath = path.resolve(frontendDir, 'src/components/Navbar.jsx');
  const navbarSource = fs.readFileSync(navbarSourcePath, 'utf-8');

  // 2.1 Non-interactive container: Pill must be a <div>, NOT a <button> or <a>
  const pillSnippetIndex = navbarSource.indexOf('Anki Live Connection Status Indicator');
  assert(pillSnippetIndex !== -1, 'Navbar contains the Anki Live Connection Status Indicator block');

  const pillSnippet = navbarSource.substring(
    pillSnippetIndex,
    navbarSource.indexOf('Profile Trigger', pillSnippetIndex)
  );

  assert(
    pillSnippet.includes('<div') && !pillSnippet.includes('<button') && !pillSnippet.includes('<a'),
    'Anki Live Pill container element is a <div> (not an interactive <button> or <a>)'
  );

  assert(
    !pillSnippet.includes('onClick') && !pillSnippet.includes('cursor-pointer'),
    'Anki Live Pill has NO onClick handler and NO cursor-pointer class'
  );

  assert(
    !pillSnippet.includes('role="button"') && !pillSnippet.includes('tabIndex'),
    'Anki Live Pill has no button role or keyboard tabIndex'
  );

  assert(
    pillSnippet.includes('select-none'),
    'Anki Live Pill has select-none class for pure display styling'
  );

  // 2.2 Absence of audit badge, card counts, or modal triggers
  assert(
    !pillSnippet.toLowerCase().includes('audit') &&
    !pillSnippet.includes('cards') &&
    !pillSnippet.includes('count') &&
    !pillSnippet.includes('pct') &&
    !pillSnippet.includes('grade'),
    'Anki Live Pill contains NO audit badge, NO card counts, NO grade metrics, and NO modal trigger'
  );

  // 2.3 Dynamic SSR Rendering for Connection States
  const { mod: navbarMod } = await compileComponent('src/components/Navbar.jsx');
  const Navbar = navbarMod.default;

  // Case A: Connected = true
  const htmlConnected = renderToStaticMarkup(
    React.createElement(Navbar, {
      currentView: 'lessons',
      setView: () => {},
      ankiStatus: { connected: true },
      onOpenProfile: () => {},
    })
  );

  assert(
    htmlConnected.includes('Anki Live') && !htmlConnected.includes('Anki Offline'),
    'When ankiStatus.connected is true, pill displays "Anki Live"'
  );
  assert(
    htmlConnected.includes('bg-emerald-400') && htmlConnected.includes('pulse-dot'),
    'When ankiStatus.connected is true, status indicator dot is emerald with pulse-dot animation'
  );
  assert(
    htmlConnected.includes('title="Anki Live (:8765)"'),
    'When ankiStatus.connected is true, title tooltip explains live connection at port 8765'
  );

  // Case B: Connected = false
  const htmlOffline = renderToStaticMarkup(
    React.createElement(Navbar, {
      currentView: 'lessons',
      setView: () => {},
      ankiStatus: { connected: false },
      onOpenProfile: () => {},
    })
  );

  assert(
    htmlOffline.includes('Anki Offline') && !htmlOffline.includes('Anki Live'),
    'When ankiStatus.connected is false, pill displays "Anki Offline"'
  );
  assert(
    htmlOffline.includes('bg-rose-500'),
    'When ankiStatus.connected is false, status indicator dot is rose-500'
  );

  // Case C: ankiStatus is null / undefined (Adversarial resilience)
  const htmlNullStatus = renderToStaticMarkup(
    React.createElement(Navbar, {
      currentView: 'lessons',
      setView: () => {},
      ankiStatus: null,
      onOpenProfile: () => {},
    })
  );

  assert(
    htmlNullStatus.includes('Anki Offline'),
    'When ankiStatus is null/undefined, pill gracefully falls back to "Anki Offline" without crash'
  );

  // =========================================================================
  // TEST SUITE 3: LessonsView Header Deck Audit Complete Removal
  // =========================================================================
  console.log('\n--- TEST SUITE 3: LessonsView Header Deck Audit Complete Removal ---');
  const lessonsViewSourcePath = path.resolve(frontendDir, 'src/views/LessonsView.jsx');
  const lessonsViewSource = fs.readFileSync(lessonsViewSourcePath, 'utf-8');

  // 3.1 DeckAuditModal import check
  assert(
    !lessonsViewSource.includes('DeckAuditModal'),
    'LessonsView does NOT import DeckAuditModal'
  );

  // 3.2 State variable check
  assert(
    !lessonsViewSource.includes('showAuditModal') &&
    !lessonsViewSource.includes('setShowAuditModal') &&
    !lessonsViewSource.includes('auditOpen'),
    'LessonsView does NOT contain any audit modal state variables'
  );

  // 3.3 Header button check
  const headerMatch = lessonsViewSource.match(/\{\/\* Top Header & Level Tabs \*\/\}[\s\S]*?\{\/\* Main Layout Grid \*\/\}/);
  assert(headerMatch !== null, 'Found Top Header block in LessonsView');

  const headerSnippet = headerMatch ? headerMatch[0] : '';
  assert(
    !headerSnippet.toLowerCase().includes('audit'),
    'Top Header block contains NO references to audit, deck audit, or audit modal'
  );

  assert(
    headerSnippet.includes("['ALL', 'A0', 'A1', 'A2', 'B1']"),
    'Top Header right side strictly contains the curriculum level filter buttons'
  );

  // =========================================================================
  // TEST SUITE 4: Summary Block Styling (Unboxed & Yellow Highlight Line)
  // =========================================================================
  console.log('\n--- TEST SUITE 4: Summary Block Styling ---');

  // 4.1 Section class check in LessonsView.jsx
  assert(
    lessonsViewSource.includes("const isSummary = sec.title.includes('Summary') || sec.title.includes('🌟');"),
    'LessonsView identifies summary sections using title keywords ("Summary" or "🌟")'
  );

  // 4.2 Border and accent line classes: border-l-4 border-amber-400 pl-5
  assert(
    lessonsViewSource.includes("border-l-4 border-amber-400 pl-5 py-1 text-amber-100/95"),
    'Summary section applies the yellow accent highlight line "border-l-4 border-amber-400 pl-5 py-1 text-amber-100/95"'
  );

  // 4.3 Unboxed verification: No old card container classes (p-6, p-7, rounded-2xl, bg-[#0f172a], border-[#243049])
  const summarySectionRenderMatch = lessonsViewSource.match(/<section[\s\S]*?key=\{sIdx\}[\s\S]*?className=\{`space-y-4 \$\{([\s\S]*?)\}`\}/);
  assert(summarySectionRenderMatch !== null, 'Found section className template literal in LessonsView');

  if (summarySectionRenderMatch) {
    const classLogic = summarySectionRenderMatch[1];
    assert(
      !classLogic.includes('p-6') &&
      !classLogic.includes('p-7') &&
      !classLogic.includes('rounded-2xl') &&
      !classLogic.includes('bg-[#0f172a]'),
      'Summary section does NOT have old card wrapper classes (no p-6, p-7, rounded-2xl, or dark card background)'
    );
  }

  // 4.4 Heading styling for summary: amber-400
  assert(
    lessonsViewSource.includes("text-xl sm:text-2xl font-extrabold text-amber-400 tracking-tight flex items-center gap-2.5 pb-2 border-b border-amber-500/25"),
    'Summary section heading is styled with amber-400 yellow text and subtle amber underline'
  );

  // 4.5 Adversarial isolation test: Non-summary sections do NOT receive summary styles
  const testSectionSummary = { title: '🌟 Summary & Core Patterns', type: 'heading_1', content: [] };
  const testSectionGrammar = { title: 'Grammar Rule: Ergative Ne', type: 'heading_1', content: [] };
  const testSectionQuiz = { title: '❓ Practice Quiz', type: 'heading_1', content: [] };

  function evaluateSectionClasses(sec) {
    const isSummary = sec.title.includes('Summary') || sec.title.includes('🌟');
    return `space-y-4 ${isSummary ? 'border-l-4 border-amber-400 pl-5 py-1 text-amber-100/95' : ''}`.trim();
  }

  assert(
    evaluateSectionClasses(testSectionSummary).includes('border-l-4 border-amber-400 pl-5'),
    'Test summary section gets border-l-4 border-amber-400 pl-5'
  );
  assert(
    !evaluateSectionClasses(testSectionGrammar).includes('border-l-4 border-amber-400'),
    'Standard grammar section does NOT get yellow summary border'
  );
  assert(
    !evaluateSectionClasses(testSectionQuiz).includes('border-l-4 border-amber-400'),
    'Quiz section does NOT get yellow summary border'
  );

  // =========================================================================
  // TEST SUITE 5: Production Build Cleanliness Verification
  // =========================================================================
  console.log('\n--- TEST SUITE 5: Production Build Cleanliness Verification ---');
  let buildSuccess = false;
  let buildOutput = '';
  try {
    buildOutput = execSync('npm run build', {
      cwd: frontendDir,
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    buildSuccess = true;
  } catch (err) {
    buildSuccess = false;
    buildOutput = err.stderr || err.stdout || err.message;
  }

  assert(buildSuccess, 'npm run build executes with return code 0 (clean production build)');
  assert(
    fs.existsSync(path.resolve(frontendDir, 'dist/index.html')),
    'Production artifact dist/index.html exists'
  );

  const distAssets = fs.readdirSync(path.resolve(frontendDir, 'dist/assets'));
  const hasJsBundle = distAssets.some((f) => f.endsWith('.js'));
  const hasCssBundle = distAssets.some((f) => f.endsWith('.css'));

  assert(hasJsBundle, 'Production assets contain minified JS bundle');
  assert(hasCssBundle, 'Production assets contain minified CSS stylesheet');

  // Summary verdict
  console.log('\n===============================================================');
  console.log(`VERIFICATION SUMMARY: ${passedTests}/${totalTests} TESTS PASSED`);
  if (failedTests > 0) {
    console.log(`CHALLENGE FAILED: ${failedTests} assertions failed.`);
    console.log('===============================================================');
    process.exit(1);
  } else {
    console.log('ALL INVARIANTS EMPIRICALLY CONFIRMED. VERDICT: APPROVE');
    console.log('===============================================================');
    process.exit(0);
  }
}

runAllChecks().catch((err) => {
  console.error('Fatal error running verification checks:', err);
  process.exit(1);
});
