import { 
  isReferenceLesson, 
  getMasteryGrade, 
  getMasteryGradientStyle, 
  calculateLessonStats, 
  buildCurriculumAudit 
} from '../frontend/src/utils/ankiLessonAnalytics.js';

let passed = 0;
function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL: ' + msg);
    process.exit(1);
  }
  console.log('PASS: ' + msg);
  passed++;
}

// 1. Reference lesson check
assert(isReferenceLesson('A0-00'), 'A0-00 is reference lesson');
assert(isReferenceLesson('lesson_a0_00'), 'lesson_a0_00 normalizes to reference lesson');
assert(!isReferenceLesson('A1-01'), 'A1-01 is not reference lesson');

// 2. Letter grades
assert(getMasteryGrade(100) === 'A+', '100% is A+');
assert(getMasteryGrade(95) === 'A', '95% is A');
assert(getMasteryGrade(85) === 'B', '85% is B');
assert(getMasteryGrade(75) === 'C', '75% is C');
assert(getMasteryGrade(65) === 'D', '65% is D');
assert(getMasteryGrade(50) === 'F', '50% is F');
assert(getMasteryGrade(30) === 'F', '30% is F');
assert(getMasteryGrade(null) === 'Ref', 'null is Ref');

// 3. Gradient styles and exact Hue formula: Hue = max(0, min(1, (P - 50) / 50)) * 120
const g100 = getMasteryGradientStyle(100);
assert(g100.background.includes('hsla(120,'), '100% hue is 120 (green)');
const g75 = getMasteryGradientStyle(75);
assert(g75.background.includes('hsla(60,'), '75% hue is 60 (yellow)');
const g50 = getMasteryGradientStyle(50);
assert(g50.background.includes('hsla(0,'), '50% hue is 0 (red)');
const g30 = getMasteryGradientStyle(30);
assert(g30.background.includes('hsla(0,'), '<50% clamped hue is 0 (red)');

// 4. calculateLessonStats on A0-00 (0 cards)
const a0Stats = calculateLessonStats([], 'A0-00');
assert(a0Stats.isReference === true, 'A0-00 isReference is true');
assert(a0Stats.isDeficit === false, 'A0-00 isDeficit is false');
assert(a0Stats.deficitCount === 0, 'A0-00 deficitCount is 0');
assert(a0Stats.grade === 'Ref', 'A0-00 grade is Ref');
assert(a0Stats.masteryPct === null, 'A0-00 masteryPct is null');

// 5. Standard lesson deficit (< 5 cards)
const dummyCards = [
  { lesson_codes: ['A1-01'], status: 'Mastered' },
  { lesson_codes: ['A1-01'], status: 'Learning' }
];
const a1Stats = calculateLessonStats(dummyCards, 'A1-01');
assert(a1Stats.isReference === false, 'A1-01 isReference is false');
assert(a1Stats.isDeficit === true, 'A1-01 (2 cards) isDeficit is true');
assert(a1Stats.deficitCount === 3, 'A1-01 deficitCount is 3');
assert(a1Stats.totalCards === 2, 'A1-01 totalCards is 2');
assert(a1Stats.masteryPct === 50, 'A1-01 masteryPct is 50');
assert(a1Stats.learningPct === 50, 'A1-01 learningPct is 50');
assert(a1Stats.strugglingPct === 0, 'A1-01 strugglingPct is 0');

// 6. Standard lesson non-deficit (>= 5 cards) with 3-way breakdown
const dummyCardsFull = [
  { lesson_codes: ['A1-02'], status: 'Mastered' },
  { lesson_codes: ['A1-02'], status: 'Mastered' },
  { lesson_codes: ['A1-02'], status: 'Mastered' },
  { lesson_codes: ['A1-02'], status: 'Learning' },
  { lesson_codes: ['A1-02'], status: 'Struggling' }
];
const a2Stats = calculateLessonStats(dummyCardsFull, 'A1-02');
assert(a2Stats.isDeficit === false, 'A1-02 (5 cards) isDeficit is false');
assert(a2Stats.totalCards === 5, 'A1-02 totalCards is 5');
assert(a2Stats.masteryPct === 60, '3/5 is 60% mastery');
assert(a2Stats.learningPct === 20, '1/5 is 20% learning');
assert(a2Stats.strugglingPct === 20, '1/5 is 20% struggling');
assert(a2Stats.grade === 'D', '60% grade is D');

// 7. buildCurriculumAudit excludes A0-00 from deficit count
const audit = buildCurriculumAudit([{ code: 'A0-00' }, { code: 'A1-01' }], dummyCards);
assert(audit.deficitCount === 1, 'Only A1-01 counted in deficitCount, A0-00 excluded');

console.log(`\nALL ${passed} UNIT TESTS PASSED SUCCESSFULLY!`);
