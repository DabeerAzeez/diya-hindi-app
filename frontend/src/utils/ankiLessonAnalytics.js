/**
 * Anki & Lesson Analytics Utility
 * Maps cards to curriculum lesson modules, computes mastery grades,
 * and detects card deficits (< 5 cards).
 */

export const MIN_CARDS_PER_LESSON = 5;
export const REFERENCE_LESSONS = ['A0-00'];

/**
 * Determine whether a lesson code corresponds to a reference lesson (e.g. A0-00)
 */
export function isReferenceLesson(code) {
  if (!code) return false;
  return REFERENCE_LESSONS.includes(normalizeLessonCode(code));
}

/**
 * Letter grade calculation based on percentage score.
 */
export function getMasteryGrade(pct) {
  if (pct === null || pct === undefined) return 'Ref';
  if (pct >= 100) return 'A+';
  if (pct >= 90) return 'A';
  if (pct >= 80) return 'B';
  if (pct >= 70) return 'C';
  if (pct >= 60) return 'D';
  return 'F';
}

/**
 * Continuous HSL gradient (A+ 100% to F <= 50%, formula: Hue = max(0, min(1, (P - 50) / 50)) * 120)
 */
export function getMasteryGradientStyle(pct) {
  if (pct === null || pct === undefined) {
    return {
      background: 'rgba(51, 65, 85, 0.4)',
      border: '1px solid rgba(71, 85, 105, 0.6)',
      color: '#94a3b8',
    };
  }
  const clampedRatio = Math.max(0, Math.min(1, (pct - 50) / 50));
  const hue = Math.round(clampedRatio * 120);
  return {
    background: `hsla(${hue}, 80%, 45%, 0.15)`,
    border: `1px solid hsla(${hue}, 80%, 45%, 0.35)`,
    color: `hsl(${hue}, 85%, 65%)`,
  };
}

/**
 * Standardize lesson code representation (e.g. 'a0_01' -> 'A0-01')
 */
export function normalizeLessonCode(code) {
  if (!code || typeof code !== 'string') return '';
  return code
    .toUpperCase()
    .replace(/^LESSON[_\-\s:]*/i, '')
    .replace(/_/g, '-')
    .trim();
}

/**
 * Filter all cards that practice or relate to a specific lesson code.
 */
export function getCardsForLesson(cards = [], lessonCode = '') {
  const safeCards = Array.isArray(cards) ? cards : [];
  if (!lessonCode || !safeCards.length) return [];
  const target = normalizeLessonCode(lessonCode).toLowerCase();
  const targetUnderscore = target.replace(/-/g, '_');

  return safeCards.filter((c) => {
    if (!c || typeof c !== 'object') return false;

    // 1. Direct match on processed lesson_codes array
    if (Array.isArray(c.lesson_codes)) {
      if (c.lesson_codes.some((code) => normalizeLessonCode(code).toLowerCase() === target)) {
        return true;
      }
    }

    // 2. Direct match on primary_lesson
    if (c.primary_lesson && normalizeLessonCode(c.primary_lesson).toLowerCase() === target) {
      return true;
    }

    // 3. Match within raw tags
    const tags = Array.isArray(c.tags) ? c.tags : [];
    for (const tag of tags) {
      const lowerTag = tag.toLowerCase();
      if (
        lowerTag === `lesson::${target}` ||
        lowerTag === `lesson::${targetUnderscore}` ||
        lowerTag === `lesson_${targetUnderscore}` ||
        lowerTag === target
      ) {
        return true;
      }
    }

    return false;
  });
}

/**
 * Calculate performance metrics and grade for a specific lesson.
 */
export function calculateLessonStats(cards = [], lessonCode = '', minThreshold = MIN_CARDS_PER_LESSON) {
  const safeCards = Array.isArray(cards) ? cards : [];
  const target = normalizeLessonCode(lessonCode).toLowerCase();
  const lessonCards = getCardsForLesson(safeCards, lessonCode);
  const totalCards = lessonCards.length;

  // Grade attribution: only cards whose most complicated / highest prerequisite topic is this lesson
  const gradingCards = safeCards.filter(
    (c) => c && c.primary_lesson && normalizeLessonCode(c.primary_lesson).toLowerCase() === target
  );
  const gradingTotal = gradingCards.length;

  let mastered = 0;
  let learning = 0;
  let struggling = 0;

  // Base marks on gradingCards (or fallback to lessonCards if grading pool is empty but lesson cards exist)
  const cardsToGrade = gradingTotal > 0 ? gradingCards : lessonCards;
  const gradeBasisCount = cardsToGrade.length;

  cardsToGrade.forEach((c) => {
    if (c.status === 'Mastered') mastered++;
    else if (c.status === 'Struggling') struggling++;
    else learning++;
  });

  const isReference = isReferenceLesson(lessonCode);
  if (isReference) {
    const gradientStyle = getMasteryGradientStyle(null);
    return {
      cards: lessonCards,
      gradingCards,
      totalCards,
      gradingTotal,
      mastered,
      learning,
      struggling,
      masteryPct: null,
      learningPct: null,
      strugglingPct: null,
      grade: 'Ref',
      gradeLabel: 'Reference Lesson',
      gradeBadge: 'Ref',
      gradientStyle,
      isDeficit: false,
      deficitCount: 0,
      isReference: true,
      statusKey: 'reference',
    };
  }

  const masteryPct = gradeBasisCount > 0 ? Math.round((mastered / gradeBasisCount) * 100) : 0;
  const learningPct = gradeBasisCount > 0 ? Math.round((learning / gradeBasisCount) * 100) : 0;
  const strugglingPct = gradeBasisCount > 0 ? Math.round((struggling / gradeBasisCount) * 100) : 0;
  const isDeficit = totalCards < minThreshold;
  const deficitCount = Math.max(0, minThreshold - totalCards);

  const grade = getMasteryGrade(masteryPct);
  const gradientStyle = getMasteryGradientStyle(masteryPct);

  let statusKey = 'learning';
  let gradeLabel = `Grade: ${grade} (${masteryPct}%)`;
  let gradeBadge = `${grade} (${masteryPct}%)`;

  if (totalCards === 0) {
    statusKey = 'empty';
    gradeLabel = 'Grade: F (0%)';
    gradeBadge = 'F (0%)';
  } else if (isDeficit) {
    statusKey = 'deficit';
  } else if (strugglingPct >= 25 && struggling >= 2) {
    statusKey = 'struggling';
  } else if (masteryPct >= 80) {
    statusKey = 'mastered';
  } else if (masteryPct >= 65) {
    statusKey = 'solid';
  }

  return {
    cards: lessonCards,
    totalCards,
    mastered,
    learning,
    struggling,
    masteryPct,
    learningPct,
    strugglingPct,
    grade,
    gradeLabel,
    gradeBadge,
    gradientStyle,
    isDeficit,
    deficitCount,
    isReference: false,
    statusKey,
  };
}

/**
 * Aggregates full curriculum scorecard and audit metrics.
 */
export function buildCurriculumAudit(lessons = [], cards = [], minThreshold = MIN_CARDS_PER_LESSON) {
  const safeCards = Array.isArray(cards) ? cards : [];
  const safeLessons = Array.isArray(lessons) ? lessons : [];

  let totalMasteredCards = 0;
  let totalLearningCards = 0;
  let totalStrugglingCards = 0;

  safeCards.forEach((c) => {
    if (!c || typeof c !== 'object') return;
    if (c.status === 'Mastered') totalMasteredCards++;
    else if (c.status === 'Struggling') totalStrugglingCards++;
    else totalLearningCards++;
  });

  const auditItems = safeLessons.map((lesson) => {
    if (!lesson || typeof lesson !== 'object') return null;
    const code = lesson.code || '';
    const stats = calculateLessonStats(safeCards, code, minThreshold);
    return {
      id: lesson.id || code,
      slug: lesson.slug,
      code,
      title: lesson.title,
      ...stats,
    };
  }).filter(Boolean);

  const deficitLessons = auditItems.filter((i) => i.isDeficit && !i.isReference);
  const strugglingLessons = auditItems.filter((i) => i.statusKey === 'struggling' || i.struggling > 0);
  const masteredLessons = auditItems.filter((i) => i.statusKey === 'mastered' || i.statusKey === 'solid');

  const globalRetention = safeCards.length > 0 
    ? Math.round((totalMasteredCards / safeCards.length) * 100) 
    : 0;

  return {
    totalDeckCards: safeCards.length,
    totalMasteredCards,
    totalLearningCards,
    totalStrugglingCards,
    globalRetention,
    auditItems,
    deficitCount: deficitLessons.length,
    strugglingCount: strugglingLessons.length,
    masteredCount: masteredLessons.length,
  };
}
