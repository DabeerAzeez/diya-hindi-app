/**
 * Adversarial Stress Test Suite for Milestone M1
 * Tests mathematical models, gradients, deficit boundaries, reference immunity,
 * 3-way percentages, and null/undefined robustness.
 */

import {
  isReferenceLesson,
  getMasteryGrade,
  getMasteryGradientStyle,
  normalizeLessonCode,
  getCardsForLesson,
  calculateLessonStats,
  buildCurriculumAudit,
  MIN_CARDS_PER_LESSON
} from '../frontend/src/utils/ankiLessonAnalytics.js';

let passedTests = 0;
let failedTests = 0;
const failures = [];

function check(label, condition, details = '') {
  if (condition) {
    console.log(`  [PASS] ${label}`);
    passedTests++;
  } else {
    console.error(`  [FAIL] ${label} - ${details}`);
    failedTests++;
    failures.push({ label, details });
  }
}

console.log('====================================================');
console.log('STARTING EMPIRICAL ADVERSARIAL STRESS TEST SUITE');
console.log('====================================================\n');

// ----------------------------------------------------
// 1. Continuous Green-to-Red HSL Gradient
// ----------------------------------------------------
console.log('Suite 1: Continuous Green-to-Red HSL Gradient');

function extractHue(style) {
  if (!style || !style.background) return null;
  const match = style.background.match(/hsla\((\d+),/);
  return match ? Number(match[1]) : null;
}

const gradientTestValues = [
  { pct: 0, expectedHue: 0, desc: '0% must be pure red (Hue = 0)' },
  { pct: 25, expectedHue: 0, desc: '25% must be pure red (Hue = 0)' },
  { pct: 50, expectedHue: 0, desc: '50% must be strictly Hue = 0' },
  { pct: 50.1, expectedHue: 0, desc: '50.1% rounded hue must be 0' },
  { pct: 75, expectedHue: 60, desc: '75% must be yellow (Hue = 60)' },
  { pct: 99.9, expectedHue: 120, desc: '99.9% rounded hue must be 120' },
  { pct: 100, expectedHue: 120, desc: '100% must be strictly Hue = 120 (pure green)' },
  { pct: 150, expectedHue: 120, desc: '>100% (150%) must be clamped to Hue = 120' },
  { pct: -20, expectedHue: 0, desc: '<0% (-20%) must be clamped to Hue = 0' }
];

gradientTestValues.forEach(({ pct, expectedHue, desc }) => {
  const style = getMasteryGradientStyle(pct);
  const hue = extractHue(style);
  check(
    `getMasteryGradientStyle(${pct}): ${desc}`,
    hue === expectedHue,
    `Expected hue ${expectedHue}, got ${hue} (background: ${style.background})`
  );
});

// Verify strictly 120 at 100% and strictly 0 at <= 50%
const hue100 = extractHue(getMasteryGradientStyle(100));
check('Gradient Hue is strictly 120 at 100%', hue100 === 120, `Got ${hue100}`);

const hue50 = extractHue(getMasteryGradientStyle(50));
const hue25 = extractHue(getMasteryGradientStyle(25));
const hue0 = extractHue(getMasteryGradientStyle(0));
check('Gradient Hue is strictly 0 at <= 50%', hue50 === 0 && hue25 === 0 && hue0 === 0, 
  `Hues: 50% -> ${hue50}, 25% -> ${hue25}, 0% -> ${hue0}`);

// ----------------------------------------------------
// 2. Deficit Boundary Testing
// ----------------------------------------------------
console.log('\nSuite 2: Deficit Boundary Testing (0, 4, 5, 6 cards)');

const boundaryCards = (n) => Array.from({ length: n }, (_, i) => ({
  primary_lesson: 'A1-05',
  status: 'Mastered'
}));

const test0 = calculateLessonStats(boundaryCards(0), 'A1-05');
check('Deficit at 0 cards: isDeficit === true', test0.isDeficit === true && test0.deficitCount === 5,
  `isDeficit: ${test0.isDeficit}, deficitCount: ${test0.deficitCount}`);

const test4 = calculateLessonStats(boundaryCards(4), 'A1-05');
check('Deficit at 4 cards: isDeficit === true', test4.isDeficit === true && test4.deficitCount === 1,
  `isDeficit: ${test4.isDeficit}, deficitCount: ${test4.deficitCount}`);

const test5 = calculateLessonStats(boundaryCards(5), 'A1-05');
check('Deficit at 5 cards: isDeficit === false', test5.isDeficit === false && test5.deficitCount === 0,
  `isDeficit: ${test5.isDeficit}, deficitCount: ${test5.deficitCount}`);

const test6 = calculateLessonStats(boundaryCards(6), 'A1-05');
check('Deficit at 6 cards: isDeficit === false', test6.isDeficit === false && test6.deficitCount === 0,
  `isDeficit: ${test6.isDeficit}, deficitCount: ${test6.deficitCount}`);

check('Deficit triggers strictly when totalCards < 5',
  test0.isDeficit === true && test4.isDeficit === true && test5.isDeficit === false && test6.isDeficit === false,
  'Boundary condition failed'
);

// ----------------------------------------------------
// 3. Reference Lesson Testing (A0-00)
// ----------------------------------------------------
console.log('\nSuite 3: Reference Lesson Testing (A0-00)');

const refCounts = [0, 1, 4, 5, 10];
refCounts.forEach(count => {
  const cards = Array.from({ length: count }, () => ({ primary_lesson: 'A0-00', status: 'Mastered' }));
  const stats = calculateLessonStats(cards, 'A0-00');
  check(`A0-00 with ${count} cards: isReference === true`, stats.isReference === true);
  check(`A0-00 with ${count} cards: isDeficit === false`, stats.isDeficit === false);
  check(`A0-00 with ${count} cards: deficitCount === 0`, stats.deficitCount === 0);
  check(`A0-00 with ${count} cards: grade === 'Ref'`, stats.grade === 'Ref');
  check(`A0-00 with ${count} cards: masteryPct === null`, stats.masteryPct === null);
});

// Normalization variations for A0-00
['a0_00', 'lesson_a0_00', 'LESSON-A0-00', 'Lesson a0-00'].forEach(variant => {
  const stats = calculateLessonStats([], variant);
  check(`A0-00 normalization variant "${variant}" is recognized as reference`,
    stats.isReference === true && stats.isDeficit === false && stats.grade === 'Ref',
    `isReference: ${stats.isReference}, grade: ${stats.grade}`
  );
});

// ----------------------------------------------------
// 4. Three-Way Percentage Breakdown & NaN Safety
// ----------------------------------------------------
console.log('\nSuite 4: Three-Way Percentage Breakdown & Zero/NaN Handling');

const statsZero = calculateLessonStats([], 'A1-01');
check('0 cards: masteryPct is 0, not NaN', statsZero.masteryPct === 0 && !Number.isNaN(statsZero.masteryPct));
check('0 cards: learningPct is 0, not NaN', statsZero.learningPct === 0 && !Number.isNaN(statsZero.learningPct));
check('0 cards: strugglingPct is 0, not NaN', statsZero.strugglingPct === 0 && !Number.isNaN(statsZero.strugglingPct));
check('0 cards: percentages sum cleanly to 0', 
  statsZero.masteryPct + statsZero.learningPct + statsZero.strugglingPct === 0);

const partitions = [
  { m: 5, l: 0, s: 0, expectedSum: 100 },
  { m: 3, l: 1, s: 1, expectedSum: 100 },
  { m: 2, l: 2, s: 1, expectedSum: 100 },
  { m: 1, l: 1, s: 1, expectedSum: 99 }, // 33 + 33 + 33 = 99 due to integer rounding
  { m: 6, l: 1, s: 0, expectedSum: 100 },
  { m: 10, l: 5, s: 5, expectedSum: 100 },
  { m: 1, l: 2, s: 4, expectedSum: 100 }
];

partitions.forEach(({ m, l, s, expectedSum }) => {
  const cards = [
    ...Array.from({ length: m }, () => ({ primary_lesson: 'A1-02', status: 'Mastered' })),
    ...Array.from({ length: l }, () => ({ primary_lesson: 'A1-02', status: 'Learning' })),
    ...Array.from({ length: s }, () => ({ primary_lesson: 'A1-02', status: 'Struggling' }))
  ];
  const res = calculateLessonStats(cards, 'A1-02');
  const sum = res.masteryPct + res.learningPct + res.strugglingPct;
  check(
    `Partition (${m}M, ${l}L, ${s}S): sum=${sum}%, no NaNs`,
    !Number.isNaN(res.masteryPct) && !Number.isNaN(res.learningPct) && !Number.isNaN(res.strugglingPct) &&
    Math.abs(sum - 100) <= 1,
    `mastery: ${res.masteryPct}%, learning: ${res.learningPct}%, struggling: ${res.strugglingPct}%, sum: ${sum}%`
  );
});

// ----------------------------------------------------
// 5. Null / Undefined Input Robustness
// ----------------------------------------------------
console.log('\nSuite 5: Null / Undefined Input Robustness');

// getMasteryGradientStyle with null/undefined/NaN
try {
  const styleNull = getMasteryGradientStyle(null);
  check('getMasteryGradientStyle(null) does not throw', !!styleNull && styleNull.color === '#94a3b8');
} catch (err) {
  check('getMasteryGradientStyle(null) does not throw', false, err.message);
}

try {
  const styleUndef = getMasteryGradientStyle(undefined);
  check('getMasteryGradientStyle(undefined) does not throw', !!styleUndef && styleUndef.color === '#94a3b8');
} catch (err) {
  check('getMasteryGradientStyle(undefined) does not throw', false, err.message);
}

try {
  const styleNaN = getMasteryGradientStyle(NaN);
  check('getMasteryGradientStyle(NaN) does not throw', !!styleNaN);
} catch (err) {
  check('getMasteryGradientStyle(NaN) does not throw', false, err.message);
}

// calculateLessonStats with undefined inputs
try {
  const undefRes = calculateLessonStats(undefined, undefined);
  check('calculateLessonStats(undefined, undefined) does not throw', !!undefRes);
} catch (err) {
  check('calculateLessonStats(undefined, undefined) does not throw', false, err.message);
}

try {
  const emptyRes = calculateLessonStats([], undefined);
  check('calculateLessonStats([], undefined) does not throw', !!emptyRes);
} catch (err) {
  check('calculateLessonStats([], undefined) does not throw', false, err.message);
}

try {
  const undefCardsRes = calculateLessonStats(undefined, 'A1-01');
  check('calculateLessonStats(undefined, "A1-01") does not throw', !!undefCardsRes && undefCardsRes.totalCards === 0);
} catch (err) {
  check('calculateLessonStats(undefined, "A1-01") does not throw', false, err.message);
}

try {
  const nullLessonCodeRes = calculateLessonStats([], null);
  check('calculateLessonStats([], null) does not throw', !!nullLessonCodeRes && nullLessonCodeRes.totalCards === 0);
} catch (err) {
  check('calculateLessonStats([], null) does not throw', false, err.message);
}

// calculateLessonStats with null cards (ADVERSARIAL STRESS TEST)
try {
  const nullCardsRes = calculateLessonStats(null, 'A1-01');
  check('calculateLessonStats(null, "A1-01") does not throw', !!nullCardsRes, 'Returned result safely');
} catch (err) {
  check('calculateLessonStats(null, "A1-01") does not throw', false, `CRASHED with ${err.name}: ${err.message}`);
}

try {
  const nullCardsRefRes = calculateLessonStats(null, 'A0-00');
  check('calculateLessonStats(null, "A0-00") does not throw', !!nullCardsRefRes, 'Returned result safely');
} catch (err) {
  check('calculateLessonStats(null, "A0-00") does not throw', false, `CRASHED with ${err.name}: ${err.message}`);
}

try {
  const nullElementRes = calculateLessonStats([null], 'A1-01');
  check('calculateLessonStats([null], "A1-01") does not throw', !!nullElementRes, 'Returned result safely');
} catch (err) {
  check('calculateLessonStats([null], "A1-01") does not throw', false, `CRASHED with ${err.name}: ${err.message}`);
}

// buildCurriculumAudit with null inputs (ADVERSARIAL STRESS TEST)
try {
  const nullAuditRes = buildCurriculumAudit(null, null);
  check('buildCurriculumAudit(null, null) does not throw', !!nullAuditRes, 'Returned result safely');
} catch (err) {
  check('buildCurriculumAudit(null, null) does not throw', false, `CRASHED with ${err.name}: ${err.message}`);
}

console.log('\n====================================================');
console.log(`TEST SUMMARY: ${passedTests} passed, ${failedTests} failed out of ${passedTests + failedTests} checks.`);
console.log('====================================================');

if (failedTests > 0) {
  console.log('\nFAILED CHECKS DETAILS:');
  failures.forEach((f, i) => {
    console.log(`  ${i + 1}. ${f.label} -> ${f.details}`);
  });
  process.exit(1);
} else {
  console.log('\nALL ADVERSARIAL STRESS TESTS PASSED!');
  process.exit(0);
}
