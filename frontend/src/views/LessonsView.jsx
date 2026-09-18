import React, { useState, useEffect, useMemo } from 'react';
import { RenderMath } from '../utils/katexRenderer';
import { 
  ChevronRight, ChevronDown, CheckCircle2, 
  Layers, Eye,
  Lock, LockOpen, AlertTriangle, Sparkles
} from 'lucide-react';
import { 
  calculateLessonStats, 
  MIN_CARDS_PER_LESSON 
} from '../utils/ankiLessonAnalytics';
import LessonCardsModal from '../components/LessonCardsModal';
import { getLessons, getLesson, getAnkiCards } from '../services/api';

export default function LessonsView() {
  const [lessons, setLessons] = useState([]);
  const [selectedSlug, setSelectedSlug] = useState(null);
  const [lessonDetail, setLessonDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [ankiCards, setAnkiCards] = useState([]);
  const [showInspectModal, setShowInspectModal] = useState(false);
  const [inspectLesson, setInspectLesson] = useState(null);
  const [inspectCards, setInspectCards] = useState(null);
  const [inspectStats, setInspectStats] = useState(null);
  const [unlockedLessons, setUnlockedLessons] = useState(() => {
    try {
      const saved = localStorage.getItem('diya_unlocked_lessons');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [showUnlockModal, setShowUnlockModal] = useState(false);

  // Check whether a lesson is unlocked
  const isLessonUnlocked = (lesson) => {
    if (!lesson) return false;
    const code = lesson.code || '';
    // Foundations (A0 and A1) are unlocked by default
    if (code.startsWith('A0') || code.startsWith('A1')) {
      return true;
    }
    // Check localStorage unlocked list for A2 and B1 modules
    return unlockedLessons.includes(code) || unlockedLessons.includes(lesson.slug);
  };

  const handleUnlockLesson = () => {
    if (!lessonDetail) return;
    const code = lessonDetail.code;
    const slug = lessonDetail.slug;
    const updated = Array.from(new Set([...unlockedLessons, code, slug]));
    setUnlockedLessons(updated);
    try {
      localStorage.setItem('diya_unlocked_lessons', JSON.stringify(updated));
    } catch (e) {
      console.error('Failed to save to localStorage', e);
    }
    setShowUnlockModal(false);
  };

  const handleRelockLesson = (e) => {
    e?.stopPropagation();
    if (!lessonDetail) return;
    const code = lessonDetail.code;
    const slug = lessonDetail.slug;
    const updated = unlockedLessons.filter((item) => item !== code && item !== slug);
    setUnlockedLessons(updated);
    try {
      localStorage.setItem('diya_unlocked_lessons', JSON.stringify(updated));
    } catch (e) {
      console.error('Failed to save to localStorage', e);
    }
  };

  useEffect(() => {
    getLessons()
      .then((data) => {
        setLessons(data);
        if (data.length > 0) {
          setSelectedSlug(data[0].slug);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching lessons:', err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedSlug) return;
    setLoadingDetail(true);
    getLesson(selectedSlug)
      .then((data) => {
        setLessonDetail(data);
        setLoadingDetail(false);
      })
      .catch((err) => {
        console.error('Error fetching lesson detail:', err);
        setLoadingDetail(false);
      });
  }, [selectedSlug]);

  // Load Anki cards on mount for sidebar badges and in-lesson scoring
  useEffect(() => {
    getAnkiCards()
      .then((data) => {
        setAnkiCards(data.cards || []);
      })
      .catch((err) => console.error('Error fetching Anki cards:', err));
  }, []);

  const filteredLessons = lessons.filter((l) => {
    if (levelFilter === 'ALL') return true;
    if (levelFilter === 'A0') return l.code.includes('A0');
    if (levelFilter === 'A1') return l.code.includes('A1');
    if (levelFilter === 'A2') return l.code.includes('A2');
    if (levelFilter === 'B1') return l.code.includes('B1');
    return true;
  });

  // Calculate stats for current lesson
  const currentCode = lessonDetail?.code || '';
  const currentLessonStats = useMemo(() => {
    return calculateLessonStats(ankiCards, currentCode, MIN_CARDS_PER_LESSON);
  }, [ankiCards, currentCode]);

  const quizStartIndex = lessonDetail?.sections?.findIndex(
    (s) => s.title.includes('Quiz') || s.title.includes('❓')
  ) ?? -1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      
      {/* Top Header & Level Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 pb-6 border-b border-[#243049]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <span>📖 Lessons</span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {lessons.length} Modules
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Master sequential grammar patterns, dialogues, and practice quizzes.
          </p>
        </div>

        {/* Level Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center bg-[#151d2f] p-1 rounded-xl border border-[#243049] text-xs">
            {['ALL', 'A0', 'A1', 'A2', 'B1'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                  levelFilter === lvl
                    ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {lvl === 'ALL' ? 'All Levels' : `Level ${lvl}`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Lesson Directory */}
        <div className="lg:col-span-4 bg-[#151d2f] rounded-2xl border border-[#243049] p-4 max-h-[calc(100vh-220px)] overflow-y-auto space-y-1.5">
          <div className="px-3 py-2 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-[#243049]/50 mb-2 flex items-center justify-between">
            <span>Lesson Catalog</span>
            <span className="text-[11px] text-slate-500 font-normal lowercase">({filteredLessons.length})</span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-sm text-slate-400">Loading lessons...</div>
          ) : filteredLessons.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500">No lessons match filter</div>
          ) : (
            filteredLessons.map((l) => {
              const isSelected = selectedSlug === l.slug;
              const isUnlocked = isLessonUnlocked(l);
              const lStats = calculateLessonStats(ankiCards, l.code);
              return (
                <button
                  key={l.id}
                  onClick={() => setSelectedSlug(l.slug)}
                  className={`w-full text-left p-3 rounded-xl transition-all flex items-start justify-between gap-3 group ${
                    isSelected
                      ? 'bg-blue-600/20 border border-blue-500/50 text-white shadow-sm'
                      : 'hover:bg-[#1c263d] text-slate-300 border border-transparent'
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider flex items-center gap-1 ${
                        isSelected 
                          ? 'bg-blue-500 text-white' 
                          : isUnlocked
                          ? 'bg-[#243049] text-amber-400'
                          : 'bg-slate-800/90 text-slate-400 border border-slate-700/60'
                      }`}>
                        {!isUnlocked && <Lock size={10} className="text-amber-400/80 shrink-0" />}
                        <span>{l.code || 'Lesson'}</span>
                      </span>

                      {/* Anki Card Health & Deficit Micro-Badge */}
                      {lStats && (
                        lStats.isReference ? (
                          <span 
                            title="Reference Lesson (No flashcards required)"
                            className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60"
                          >
                            Ref
                          </span>
                        ) : lStats.isDeficit ? (
                          <span 
                            title={`Card Deficit: ${lStats.totalCards}/5 cards`}
                            className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1"
                          >
                            <AlertTriangle size={9} className="text-slate-400" />
                            <span>Deficit ({lStats.totalCards}/5)</span>
                          </span>
                        ) : (
                          <span 
                            title={`Mastery: ${lStats.masteryPct}% (${lStats.grade})`}
                            style={lStats.gradientStyle}
                            className="text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm"
                          >
                            {lStats.masteryPct}%
                          </span>
                        )
                      )}

                      {!isUnlocked && (
                        <span className="text-[10px] font-medium text-slate-500">
                          Locked
                        </span>
                      )}
                    </div>
                    <p className={`text-sm font-semibold truncate ${
                      !isUnlocked && !isSelected ? 'text-slate-400 group-hover:text-slate-200' : 'group-hover:text-white'
                    }`}>
                      {l.title.replace(/^Lesson\s+[A-Za-z0-9.-]+:\s*/, '')}
                    </p>
                  </div>
                  {isUnlocked ? (
                    <ChevronRight size={16} className={`mt-2 transition-transform shrink-0 ${isSelected ? 'text-blue-400 translate-x-0.5' : 'text-slate-500'}`} />
                  ) : (
                    <Lock size={14} className={`mt-2 shrink-0 ${isSelected ? 'text-amber-400' : 'text-slate-500 group-hover:text-amber-400/70'}`} />
                  )}
                </button>
              );
            })
          )}
        </div>

        {/* Center / Right Column: Lesson Reader */}
        <div className="lg:col-span-8 space-y-6">
          {loadingDetail ? (
            <div className="bg-[#151d2f] rounded-2xl border border-[#243049] p-12 text-center text-slate-400 text-sm">
              Loading lesson content...
            </div>
          ) : !lessonDetail ? (
            <div className="bg-[#151d2f] rounded-2xl border border-[#243049] p-12 text-center text-slate-500 text-sm">
              Select a lesson from the left catalog to read.
            </div>
          ) : !isLessonUnlocked(lessonDetail) ? (
            /* Locked Lesson Preview Card */
            <div className="bg-[#151d2f] rounded-2xl border border-[#243049] p-8 sm:p-12 text-center space-y-6 animate-fade-in shadow-xl relative overflow-hidden">
              {/* Subtle ambient amber glow */}
              <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

              {/* Lock Badge */}
              <div className="w-16 h-16 rounded-2xl bg-amber-500/15 border-2 border-amber-500/30 flex items-center justify-center text-amber-400 mx-auto shadow-lg shadow-amber-950/30">
                <Lock size={32} />
              </div>

              {/* Code & Level */}
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-bold uppercase tracking-wider mb-3">
                  {lessonDetail.code} • {lessonDetail.code?.startsWith('A2') ? 'Level A2 Pre-Intermediate' : lessonDetail.code?.startsWith('B1') ? 'Level B1 Intermediate' : 'Curriculum Module'}
                </div>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight max-w-xl mx-auto">
                  {lessonDetail.title}
                </h2>
              </div>

              {/* Curriculum Overview Box */}
              <div className="max-w-xl mx-auto p-5 rounded-xl bg-[#0f172a] border border-[#243049] text-sm text-slate-300 leading-relaxed text-left space-y-2.5">
                <div className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                  <Sparkles size={14} />
                  <span>Module Overview</span>
                </div>
                <p className="text-slate-300 text-xs sm:text-sm leading-relaxed">
                  {lessonDetail.sections?.[0]?.content?.[0]?.text?.replace(/\*\*/g, '') ||
                    'Master next-level grammar concepts, authentic polyglot dialogues, and practical interactive quizzes.'}
                </p>
              </div>

              {/* Lock Notice & Action */}
              <div className="pt-2 space-y-4 max-w-md mx-auto">
                <p className="text-xs text-slate-400 leading-relaxed">
                  This lesson is currently locked in your curriculum path. When you are ready to advance, click below to unlock full explanations, formulas, dialogue, and practice quizzes.
                </p>

                <button
                  onClick={() => setShowUnlockModal(true)}
                  className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-amber-500 hover:bg-amber-400 active:scale-95 text-slate-950 font-bold text-sm shadow-xl shadow-amber-500/20 transition-all cursor-pointer"
                >
                  <LockOpen size={18} />
                  <span>Unlock Lesson</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-[#151d2f] rounded-2xl border border-[#243049] p-6 sm:p-8 space-y-8 animate-fade-in shadow-xl">
              
              {/* Lesson Title Header with Status */}
              <div className="pb-6 border-b border-[#243049] flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-bold uppercase tracking-wider">
                      {lessonDetail.code || 'Lesson'}
                    </div>
                    {(lessonDetail.code?.startsWith('A2') || lessonDetail.code?.startsWith('B1')) && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[11px] font-semibold">
                        <CheckCircle2 size={12} />
                        <span>Unlocked</span>
                      </span>
                    )}
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
                    {lessonDetail.title}
                  </h2>
                </div>

                {(lessonDetail.code?.startsWith('A2') || lessonDetail.code?.startsWith('B1')) && (
                  <button
                    onClick={handleRelockLesson}
                    title="Lock this lesson again"
                    className="self-start text-xs text-slate-400 hover:text-amber-400 border border-[#243049] hover:border-amber-500/40 bg-[#0f172a] px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 shrink-0 cursor-pointer"
                  >
                    <Lock size={13} />
                    <span>Lock Lesson</span>
                  </button>
                )}
              </div>

              {/* Anki Performance Scorecard & Health Strip */}
              <div className={`p-4 sm:p-5 rounded-2xl border transition-all shadow-md ${
                currentLessonStats.isReference
                  ? 'bg-[#0f172a] border-[#243049]'
                  : currentLessonStats.isDeficit 
                  ? 'bg-slate-900/60 border-slate-700/60' 
                  : 'bg-[#0f172a] border-[#243049]'
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-white uppercase tracking-wider">
                      <Layers size={15} className="text-indigo-400" />
                      <span>Anki Mastery Grade:</span>
                    </div>
                    <span 
                      className="text-xs px-2.5 py-0.5 rounded-full font-bold border shadow-sm"
                      style={currentLessonStats.gradientStyle}
                    >
                      {currentLessonStats.isReference ? 'Ref • Reference Lesson' : currentLessonStats.gradeLabel}
                    </span>
                    <span className="text-xs text-slate-400">
                      • {currentLessonStats.totalCards} card{currentLessonStats.totalCards === 1 ? '' : 's'} tagged
                    </span>
                  </div>

                  <button
                    onClick={() => {
                      setInspectLesson(lessonDetail);
                      setInspectCards(currentLessonStats.cards);
                      setInspectStats(currentLessonStats);
                      setShowInspectModal(true);
                    }}
                    className="self-start sm:self-auto px-3.5 py-1.5 rounded-xl bg-[#151d2f] hover:bg-[#1c263d] border border-[#243049] hover:border-indigo-500/50 text-xs font-semibold text-indigo-300 hover:text-white transition-all cursor-pointer flex items-center gap-1.5 shadow-sm"
                  >
                    <Eye size={13} />
                    <span>Inspect Cards ({currentLessonStats.totalCards})</span>
                  </button>
                </div>

                {/* Progress Bar & Breakdown */}
                {currentLessonStats.isReference ? (
                  <div className="text-xs text-slate-400 pt-1">
                    Pronunciation & Phonetics Reference Guide (No flashcards required for this module)
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="h-2.5 w-full bg-[#090d16] rounded-full overflow-hidden flex shadow-inner">
                      <div 
                        className="bg-emerald-500 transition-all" 
                        style={{ width: `${currentLessonStats.masteryPct}%` }} 
                        title={`${currentLessonStats.mastered} Mastered (${currentLessonStats.masteryPct}%)`}
                      />
                      <div 
                        className="bg-amber-400 transition-all" 
                        style={{ width: `${currentLessonStats.learningPct}%` }} 
                        title={`${currentLessonStats.learning} Learning (${currentLessonStats.learningPct}%)`}
                      />
                      <div 
                        className="bg-rose-500 transition-all" 
                        style={{ width: `${currentLessonStats.strugglingPct}%` }} 
                        title={`${currentLessonStats.struggling} Struggling (${currentLessonStats.strugglingPct}%)`}
                      />
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 flex-wrap gap-2 pt-0.5">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="text-emerald-400 font-medium">
                          {currentLessonStats.mastered} Mastered ({currentLessonStats.masteryPct}%)
                        </span>
                        <span className="text-amber-400 font-medium">
                          {currentLessonStats.learning} Learning ({currentLessonStats.learningPct}%)
                        </span>
                        <span className="text-rose-400 font-medium">
                          {currentLessonStats.struggling} Struggling ({currentLessonStats.strugglingPct}%)
                        </span>
                      </div>

                      {currentLessonStats.isDeficit && (
                        <span className="text-slate-400 font-medium flex items-center gap-1">
                          <AlertTriangle size={13} className="text-slate-400" />
                          <span>Deficit: Needs {currentLessonStats.deficitCount} more card{currentLessonStats.deficitCount > 1 ? 's' : ''} to reach 5-card baseline</span>
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Render Structured Sections */}
              <div className="space-y-8 text-slate-300 leading-relaxed text-[15px]">
                {lessonDetail.sections?.map((sec, sIdx) => {
                  const isSummary = sec.title.includes('Summary') || sec.title.includes('🌟');
                  const isQuiz = sec.title.includes('Quiz') || sec.title.includes('❓');
                  const isAfterQuizHeader = quizStartIndex !== -1 && sIdx >= quizStartIndex;
                  const isHeading1 = sec.type === 'heading_1' || isSummary || isQuiz;
                  const isHeading2 = sec.type === 'heading_2';
                  const isHeading3 = sec.type === 'heading_3';

                    // Heading styling: White for everything except Summary (which is yellow)
                    let headingStyle = 'text-base font-semibold text-white tracking-tight flex items-center gap-2 pt-2';
                    let Tag = 'h3';

                    if (isSummary) {
                      headingStyle = 'text-xl sm:text-2xl font-extrabold text-amber-400 tracking-tight flex items-center gap-2.5 pb-2 border-b border-amber-500/25';
                      Tag = 'h2';
                    } else if (isHeading1) {
                      headingStyle = 'text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5 pt-6 pb-3 border-b border-[#243049]';
                      Tag = 'h2';
                    } else if (isHeading2) {
                      headingStyle = 'text-lg sm:text-xl font-bold text-white tracking-tight flex items-center gap-2 pt-5 pb-1';
                      Tag = 'h3';
                    } else if (isHeading3) {
                      headingStyle = 'text-sm sm:text-base font-semibold text-slate-200 tracking-tight flex items-center gap-2 pt-3 pb-1';
                      Tag = 'h4';
                    }

                    return (
                      <section 
                        key={sIdx} 
                        className={`space-y-4 ${
                          isSummary 
                            ? 'border-l-4 border-amber-400 pl-5 py-1 text-amber-100/95' 
                            : ''
                        }`}
                      >
                        {/* Section Title */}
                        <Tag className={headingStyle}>
                          <RenderMath text={sec.title} />
                        </Tag>

                        {/* Section Content Items */}
                        <div className="space-y-3">
                          {sec.content?.map((item, cIdx) => {
                            const isToggle = item.type === 'toggle';
                            const hasChildren = item.children && item.children.length > 0;
                            const isQuizQuestion = 
                              isToggle ||
                              (hasChildren && (
                                isAfterQuizHeader ||
                                isQuiz ||
                                sec.title.toLowerCase().includes('question') ||
                                item.children.some(ch => typeof ch === 'string' && (ch.includes('Answer') || ch.includes('उत्तर')))
                              ));

                            // Interactive Dropdown Question (Details / Summary with blockquote answer)
                            if (isQuizQuestion) {
                              const questionTitle = item.title || item.text;
                              return (
                                <details 
                                  key={cIdx} 
                                  className="p-4 rounded-xl bg-[#0f172a] hover:bg-[#131d33] border border-[#243049] hover:border-slate-500/50 transition-all duration-200 space-y-3 group shadow-sm"
                                >
                                  <summary className="font-semibold text-white cursor-pointer flex items-center justify-between gap-4 list-none select-none [&::-webkit-details-marker]:hidden">
                                    <div className="flex-1 pr-2 leading-relaxed">
                                      <RenderMath text={questionTitle} />
                                    </div>
                                    <ChevronDown 
                                      size={18} 
                                      className="text-slate-400 group-hover:text-white group-open:rotate-180 transition-transform duration-200 shrink-0" 
                                    />
                                  </summary>
                                  <blockquote className="p-4 rounded-xl bg-amber-500/10 border-l-4 border-amber-500 text-slate-200 text-sm space-y-2 animate-fade-in my-1">
                                    {item.children?.map((ch, chIdx) => (
                                      <div key={chIdx} className="leading-relaxed">
                                        <RenderMath text={ch} />
                                      </div>
                                    ))}
                                  </blockquote>
                                </details>
                              );
                            }

                            if (item.type === 'paragraph') {
                              return (
                                <p key={cIdx} className={`${isSummary ? 'text-amber-100/90' : 'text-slate-300'} leading-relaxed`}>
                                  <RenderMath text={item.text} />
                                </p>
                              );
                            }

                            if (item.type === 'bullet' || item.type === 'numbered') {
                              return (
                                <div key={cIdx} className="flex items-start gap-2.5 ml-1">
                                  <span className={`${isSummary ? 'text-amber-400' : 'text-amber-400'} font-bold shrink-0 mt-0.5`}>•</span>
                                  <div className="space-y-1 flex-1">
                                    <div className={isSummary ? 'text-amber-100/90' : 'text-slate-300'}>
                                      <RenderMath text={item.text} />
                                    </div>
                                    {item.children?.map((ch, chIdx) => (
                                      <div key={chIdx} className={`ml-4 text-xs ${isSummary ? 'text-amber-200/75' : 'text-slate-400'}`}>
                                        <RenderMath text={ch} />
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              );
                            }

                            if (item.type === 'table') {
                              if (!item.rows || item.rows.length === 0) return null;
                              const headers = item.rows[0];
                              const rows = item.rows.slice(1);
                              return (
                                <div key={cIdx} className="overflow-x-auto rounded-xl border border-[#243049] my-4 shadow-sm">
                                  <table className="w-full text-left border-collapse text-sm">
                                    <thead>
                                      <tr className="bg-[#1c263d] border-b border-[#243049] text-white">
                                        {headers.map((h, hIdx) => (
                                          <th key={hIdx} className="px-4 py-3 font-bold text-white">
                                            <RenderMath text={h} />
                                          </th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[#243049]">
                                      {rows.map((r, rIdx) => (
                                        <tr key={rIdx} className="hover:bg-[#1f2b45]/40 transition-colors">
                                          {r.map((c, cellIdx) => (
                                            <td key={cellIdx} className="px-4 py-2.5 text-slate-300 leading-normal">
                                              <RenderMath text={c} />
                                            </td>
                                          ))}
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              );
                            }

                            if (item.type === 'quote') {
                            return (
                              <blockquote key={cIdx} className="p-4 rounded-xl bg-amber-500/10 border-l-4 border-amber-500 text-slate-200 italic my-2">
                                <RenderMath text={item.text} />
                              </blockquote>
                            );
                          }

                          return null;
                        })}
                      </div>
                    </section>
                  );
                })}
              </div>

              {(!lessonDetail.sections || lessonDetail.sections.length === 0) && lessonDetail.markdown && (
                <div className="p-6 rounded-2xl bg-[#0f172a] border border-[#243049] text-slate-300">
                  <RenderMath text={lessonDetail.markdown} />
                </div>
              )}

            </div>
          )}
        </div>

      </div>

      {/* Unlock Confirmation Warning Modal */}
      {showUnlockModal && lessonDetail && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={() => setShowUnlockModal(false)}
        >
          <div 
            className="bg-[#151d2f] border border-amber-500/40 rounded-2xl p-6 sm:p-8 max-w-lg w-full shadow-2xl shadow-black/80 space-y-6 animate-scale-up relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Warning Icon & Header */}
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0 mt-0.5 shadow-md shadow-amber-950/20">
                <AlertTriangle size={24} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg sm:text-xl font-extrabold text-white tracking-tight leading-snug">
                  Are you sure that you are ready to move on to the next lesson?
                </h3>
                <p className="text-xs text-amber-400 font-bold mt-1 uppercase tracking-wider">
                  {lessonDetail.code}: {lessonDetail.title.replace(/^Lesson\s+[A-Za-z0-9.-]+:\s*/, '')}
                </p>
              </div>
            </div>

            {/* Context Notice */}
            <div className="p-4 rounded-xl bg-[#0f172a] border border-[#243049] text-xs sm:text-sm text-slate-300 leading-relaxed space-y-2">
              <p className="text-slate-200 font-medium">
                You are about to unlock new curriculum material.
              </p>
              <p className="text-slate-400 text-xs leading-relaxed">
                Make sure you have consolidated your active vocabulary, completed earlier practice quizzes, and reviewed your pending Anki cards before tackling new grammar patterns.
              </p>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowUnlockModal(false)}
                className="px-4 py-2.5 rounded-xl border border-[#243049] hover:bg-[#1c263d] text-slate-300 hover:text-white text-xs font-semibold transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleUnlockLesson}
                className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 active:scale-95 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-amber-500/20 flex items-center gap-1.5 cursor-pointer"
              >
                <LockOpen size={15} />
                <span>Yes, Unlock Lesson</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Lesson Flashcards Inspection Modal */}
      <LessonCardsModal
        isOpen={showInspectModal}
        onClose={() => setShowInspectModal(false)}
        lesson={inspectLesson || lessonDetail}
        cards={inspectCards || currentLessonStats.cards}
        stats={inspectStats || currentLessonStats}
      />

    </div>
  );
}
