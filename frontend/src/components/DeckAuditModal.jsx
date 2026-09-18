import React, { useState, useMemo } from 'react';
import { 
  X, AlertTriangle, CheckCircle2, Sparkles, Search, Layers, 
  ArrowRight, Filter, BookOpen, ExternalLink, ShieldAlert 
} from 'lucide-react';
import { buildCurriculumAudit, MIN_CARDS_PER_LESSON } from '../utils/ankiLessonAnalytics';

export default function DeckAuditModal({ 
  isOpen, 
  onClose, 
  lessons = [], 
  cards = [], 
  onSelectLesson,
  onInspectLessonCards 
}) {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('DEFICIT'); // Default to DEFICIT to immediately highlight gaps!
  const [levelFilter, setLevelFilter] = useState('ALL');

  const audit = useMemo(() => {
    return buildCurriculumAudit(lessons, cards, MIN_CARDS_PER_LESSON);
  }, [lessons, cards]);

  if (!isOpen) return null;

  const filteredItems = audit.auditItems.filter((item) => {
    // Level filter
    if (levelFilter !== 'ALL' && !item.code.startsWith(levelFilter)) {
      return false;
    }

    // Status filter
    if (filterType === 'DEFICIT' && !item.isDeficit) return false;
    if (filterType === 'STRUGGLING' && (item.statusKey !== 'struggling' && item.struggling === 0)) return false;
    if (filterType === 'MASTERED' && (item.statusKey !== 'mastered' && item.statusKey !== 'solid')) return false;

    // Search query
    if (search) {
      const q = search.toLowerCase();
      const codeMatch = item.code.toLowerCase().includes(q);
      const titleMatch = item.title.toLowerCase().includes(q);
      if (!codeMatch && !titleMatch) return false;
    }

    return true;
  });

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="bg-[#151d2f] border border-[#243049] rounded-2xl max-w-5xl w-full max-h-[92vh] flex flex-col shadow-2xl shadow-black/90 overflow-hidden animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-6 border-b border-[#243049] flex items-start justify-between gap-4 bg-[#0f172a]/70">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Layers size={13} />
                <span>Deck Health & Audit</span>
              </span>
              <span className="text-xs text-slate-400">Curriculum Flashcard Matrix</span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              Anki Coverage & Performance Audit
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Identify lessons with card deficits (&lt; {MIN_CARDS_PER_LESSON} cards) and evaluate retention grades across the entire curriculum.
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-[#1c263d] transition-all cursor-pointer"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Top KPI Cards */}
        <div className="p-6 pb-4 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#0d1424] border-b border-[#243049]">
          
          {/* Deficit Alert KPI */}
          <div 
            onClick={() => setFilterType('DEFICIT')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
              filterType === 'DEFICIT'
                ? 'bg-amber-500/15 border-amber-500/50 shadow-md shadow-amber-950/40'
                : 'bg-[#151d2f] border-[#243049] hover:border-amber-500/30'
            }`}
          >
            <div className="flex items-center justify-between text-xs text-amber-400 font-semibold mb-1">
              <span className="flex items-center gap-1">
                <AlertTriangle size={13} />
                <span>Card Deficits</span>
              </span>
              <span className="text-[10px] bg-amber-500/20 px-1.5 py-0.2 rounded">&lt;5 cards</span>
            </div>
            <div className="text-2xl font-black text-amber-300">
              {audit.deficitCount} <span className="text-xs font-medium text-slate-400">/ {lessons.length}</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">Modules needing more flashcards</p>
          </div>

          {/* Mastered KPI */}
          <div 
            onClick={() => setFilterType('MASTERED')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
              filterType === 'MASTERED'
                ? 'bg-emerald-500/15 border-emerald-500/50 shadow-md shadow-emerald-950/40'
                : 'bg-[#151d2f] border-[#243049] hover:border-emerald-500/30'
            }`}
          >
            <div className="flex items-center justify-between text-xs text-emerald-400 font-semibold mb-1">
              <span className="flex items-center gap-1">
                <CheckCircle2 size={13} />
                <span>Mastered Modules</span>
              </span>
              <span className="text-[10px] bg-emerald-500/20 px-1.5 py-0.2 rounded">&ge;65%</span>
            </div>
            <div className="text-2xl font-black text-emerald-300">
              {audit.masteredCount} <span className="text-xs font-medium text-slate-400">/ {lessons.length}</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">{audit.totalMasteredCards} mastered cards</p>
          </div>

          {/* Struggling KPI */}
          <div 
            onClick={() => setFilterType('STRUGGLING')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
              filterType === 'STRUGGLING'
                ? 'bg-rose-500/15 border-rose-500/50 shadow-md shadow-rose-950/40'
                : 'bg-[#151d2f] border-[#243049] hover:border-rose-500/30'
            }`}
          >
            <div className="flex items-center justify-between text-xs text-rose-400 font-semibold mb-1">
              <span className="flex items-center gap-1">
                <ShieldAlert size={13} />
                <span>Struggling Weak Spots</span>
              </span>
              <span className="text-[10px] bg-rose-500/20 px-1.5 py-0.2 rounded">Lapses</span>
            </div>
            <div className="text-2xl font-black text-rose-300">
              {audit.strugglingCount} <span className="text-xs font-medium text-slate-400">modules</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">{audit.totalStrugglingCards} failing/leech cards</p>
          </div>

          {/* Total Deck Cards */}
          <div 
            onClick={() => setFilterType('ALL')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
              filterType === 'ALL'
                ? 'bg-indigo-500/15 border-indigo-500/50 shadow-md shadow-indigo-950/40'
                : 'bg-[#151d2f] border-[#243049] hover:border-indigo-500/30'
            }`}
          >
            <div className="flex items-center justify-between text-xs text-indigo-400 font-semibold mb-1">
              <span className="flex items-center gap-1">
                <Layers size={13} />
                <span>Global Deck Retention</span>
              </span>
              <span className="text-[10px] bg-indigo-500/20 px-1.5 py-0.2 rounded">{audit.globalRetention}%</span>
            </div>
            <div className="text-2xl font-black text-white">
              {audit.totalDeckCards} <span className="text-xs font-medium text-slate-400">total cards</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">Across Hindi Anki deck</p>
          </div>

        </div>

        {/* Controls Ribbon */}
        <div className="p-4 px-6 bg-[#151d2f] border-b border-[#243049] flex flex-col sm:flex-row items-center justify-between gap-3">
          
          {/* Search */}
          <div className="relative w-full sm:w-80">
            <Search size={14} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search module code or title..."
              className="w-full pl-8 pr-3 py-2 rounded-xl bg-[#0f172a] border border-[#243049] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0 text-xs">
            {/* Status Filter */}
            <div className="flex items-center bg-[#0f172a] p-1 rounded-xl border border-[#243049]">
              {[
                { id: 'ALL', label: 'All Modules' },
                { id: 'DEFICIT', label: '⚠️ Deficits Only' },
                { id: 'STRUGGLING', label: '🔴 Struggling' },
                { id: 'MASTERED', label: '🟢 Mastered' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setFilterType(tab.id)}
                  className={`px-3 py-1 rounded-lg font-medium transition-all whitespace-nowrap cursor-pointer ${
                    filterType === tab.id
                      ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Level Sub-filter */}
            <div className="flex items-center bg-[#0f172a] p-1 rounded-xl border border-[#243049]">
              {['ALL', 'A0', 'A1', 'A2', 'B1'].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setLevelFilter(lvl)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-all text-xs cursor-pointer ${
                    levelFilter === lvl
                      ? 'bg-indigo-600 text-white font-bold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

        </div>

        {/* Audit Table */}
        <div className="flex-1 overflow-y-auto p-6 pt-2">
          {filteredItems.length === 0 ? (
            <div className="p-12 text-center text-slate-400 text-sm bg-[#0f172a]/50 rounded-2xl border border-[#243049] my-4">
              <Layers size={32} className="mx-auto text-slate-600 mb-2" />
              <p className="font-semibold text-slate-300">No lessons match selected filter</p>
              <p className="text-xs text-slate-500 mt-1">Try switching to "All Modules" or clearing search.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredItems.map((item) => {
                const total = item.totalCards;
                const isDeficit = item.isDeficit;

                return (
                  <div
                    key={item.id}
                    className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group ${
                      isDeficit
                        ? 'bg-[#151d2f]/90 border-amber-500/30 hover:border-amber-500/50'
                        : item.statusKey === 'struggling'
                        ? 'bg-[#151d2f]/90 border-rose-500/30 hover:border-rose-500/50'
                        : 'bg-[#151d2f]/60 border-[#243049] hover:border-slate-600'
                    }`}
                  >
                    {/* Left: Code, Title & Coverage */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="px-2 py-0.5 rounded bg-[#243049] text-amber-400 text-[11px] font-bold uppercase tracking-wider">
                          {item.code}
                        </span>

                        {isDeficit ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
                            <AlertTriangle size={11} />
                            <span>{total === 0 ? '0 Cards Tagged' : `${total}/5 Deficit`}</span>
                          </span>
                        ) : (
                          <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                            item.statusKey === 'mastered' || item.statusKey === 'solid'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : item.statusKey === 'struggling'
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                              : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                          }`}>
                            {item.gradeBadge}
                          </span>
                        )}

                        <span className="text-xs text-slate-400">
                          {total} card{total === 1 ? '' : 's'} in deck
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-white truncate">
                        {item.title.replace(/^Lesson\s+[A-Za-z0-9\.\-]+:\s*/, '')}
                      </h4>
                    </div>

                    {/* Middle: Progress Bar Breakdown */}
                    <div className="w-full sm:w-56 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                        <span>{item.masteryPct}% Mastered</span>
                        <span className="text-slate-500">
                          {item.mastered}M • {item.learning}L • {item.struggling}S
                        </span>
                      </div>
                      
                      <div className="h-2 w-full bg-[#0b0f19] rounded-full overflow-hidden flex">
                        <div 
                          className="bg-emerald-500 transition-all" 
                          style={{ width: `${item.masteryPct}%` }} 
                          title={`${item.mastered} Mastered`}
                        />
                        <div 
                          className="bg-amber-400 transition-all" 
                          style={{ width: `${total > 0 ? (item.learning / total) * 100 : 0}%` }} 
                          title={`${item.learning} Learning`}
                        />
                        <div 
                          className="bg-rose-500 transition-all" 
                          style={{ width: `${total > 0 ? (item.struggling / total) * 100 : 0}%` }} 
                          title={`${item.struggling} Struggling`}
                        />
                      </div>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      {total > 0 && (
                        <button
                          onClick={() => {
                            onClose();
                            onInspectLessonCards?.(item, item.cards, item);
                          }}
                          className="px-3 py-1.5 rounded-lg bg-[#0f172a] hover:bg-[#1a233a] border border-[#243049] hover:border-indigo-500/40 text-xs font-semibold text-indigo-300 transition-all cursor-pointer flex items-center gap-1"
                        >
                          <Layers size={13} />
                          <span>Cards ({total})</span>
                        </button>
                      )}

                      <button
                        onClick={() => {
                          onClose();
                          onSelectLesson?.(item.slug);
                        }}
                        className="px-3.5 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600 border border-blue-500/40 text-xs font-bold text-white transition-all cursor-pointer flex items-center gap-1"
                      >
                        <BookOpen size={13} />
                        <span>Go to Lesson</span>
                      </button>
                    </div>

                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#0f172a] border-t border-[#243049] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-amber-400" />
            <span>
              Tip: Use <strong>/cards</strong> in Diya chat to automatically generate flashcards for deficit modules.
            </span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#1c263d] hover:bg-[#25324f] text-white font-medium transition-all cursor-pointer self-end sm:self-auto"
          >
            Close Audit
          </button>
        </div>

      </div>
    </div>
  );
}
