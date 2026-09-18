import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { 
  X, Layers, Search, Sparkles, AlertTriangle, CheckCircle2, 
  Eye, EyeOff 
} from 'lucide-react';

export default function LessonCardsModal({ isOpen, onClose, lesson, cards = [], stats }) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [flippedCards, setFlippedCards] = useState({});

  if (!isOpen || !lesson) return null;

  const toggleFlip = (id) => {
    setFlippedCards((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const flipAll = (state) => {
    const next = {};
    cards.forEach((c, idx) => {
      const id = c.cardId || c.noteId || idx;
      next[id] = state;
    });
    setFlippedCards(next);
  };

  const filteredCards = cards.filter((c) => {
    const front = c.front || '';
    const back = c.back || '';
    const query = search.toLowerCase();

    if (query && !front.toLowerCase().includes(query) && !back.toLowerCase().includes(query)) {
      return false;
    }

    if (statusFilter !== 'ALL' && c.status !== statusFilter) {
      return false;
    }

    return true;
  });

  const total = cards.length;
  const isDeficit = total < 5 && !stats?.isReference;

  return createPortal(
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="bg-[#151d2f] border border-[#243049] rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl shadow-black/80 overflow-hidden animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-[#243049] flex items-start justify-between gap-4 bg-[#0f172a]/60">
          <div>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-bold uppercase tracking-wider">
                {lesson.code || 'Lesson'}
              </span>
              <span className="text-xs text-slate-400">Anki Flashcard Performance</span>
              {stats?.gradeBadge && (
                <span 
                  className="text-xs px-2.5 py-0.5 rounded-full font-bold border shadow-sm"
                  style={stats.gradientStyle || {}}
                >
                  {stats.gradeBadge}
                </span>
              )}
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              {lesson.title}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-[#1c263d] transition-all cursor-pointer"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Metric Summary Ribbon */}
        <div className="px-6 py-4 bg-[#101827] border-b border-[#243049] flex items-center justify-between gap-4 flex-wrap text-xs">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-1.5 text-slate-300">
              <Layers size={15} className="text-indigo-400" />
              <span>Tagged Cards:</span>
              <span className="font-bold text-white">{total}</span>
            </div>
            <div className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 size={15} />
              <span>Mastered:</span>
              <span className="font-bold">{stats?.mastered || 0}</span>
            </div>
            <div className="flex items-center gap-1.5 text-amber-400">
              <Sparkles size={15} />
              <span>Learning:</span>
              <span className="font-bold">{stats?.learning || 0}</span>
            </div>
            <div className="flex items-center gap-1.5 text-rose-400">
              <AlertTriangle size={15} />
              <span>Struggling:</span>
              <span className="font-bold">{stats?.struggling || 0}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => flipAll(true)}
              className="text-[11px] px-2.5 py-1 rounded-lg border border-[#243049] hover:bg-[#1c263d] text-slate-300 hover:text-white transition-all cursor-pointer flex items-center gap-1"
            >
              <Eye size={12} />
              <span>Reveal All</span>
            </button>
            <button
              onClick={() => flipAll(false)}
              className="text-[11px] px-2.5 py-1 rounded-lg border border-[#243049] hover:bg-[#1c263d] text-slate-300 hover:text-white transition-all cursor-pointer flex items-center gap-1"
            >
              <EyeOff size={12} />
              <span>Hide All</span>
            </button>
          </div>
        </div>

        {/* Deficit Alert Banner if under 5 cards */}
        {isDeficit && (
          <div className="mx-6 mt-4 p-4 rounded-xl bg-slate-800/80 border border-slate-700 flex items-start gap-3 text-xs text-slate-300">
            <AlertTriangle size={18} className="text-slate-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-200">
                Card Deficit Alert ({total}/5 minimum cards)
              </p>
              <p className="text-slate-400 mt-0.5 leading-relaxed">
                This lesson currently has only {total} flashcard{total === 1 ? '' : 's'} in your Hindi deck. We recommend at least 5 cards to reliably evaluate mastery and consolidate this grammar structure.
              </p>
            </div>
          </div>
        )}

        {/* Toolbar: Search & Filter */}
        <div className="p-6 pb-3 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-72">
            <Search size={14} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search front or back..."
              className="w-full pl-8 pr-3 py-2 rounded-xl bg-[#0f172a] border border-[#243049] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0 text-xs">
            {['ALL', 'Mastered', 'Learning', 'Struggling'].map((f) => (
              <button
                key={f}
                onClick={() => setStatusFilter(f)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all whitespace-nowrap cursor-pointer ${
                  statusFilter === f
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#243049]'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Cards Scrollable Grid */}
        <div className="p-6 pt-2 overflow-y-auto flex-1 space-y-3">
          {filteredCards.length === 0 ? (
            <div className="p-12 text-center text-slate-400 text-sm bg-[#0f172a]/50 rounded-2xl border border-[#243049]">
              <Layers size={32} className="mx-auto text-slate-600 mb-2" />
              <p className="font-semibold text-slate-300">No matching flashcards found</p>
              <p className="text-xs text-slate-500 mt-1">
                {total === 0 ? 'No cards have been tagged for this lesson yet.' : 'Try adjusting your search query or status filter.'}
              </p>
            </div>
          ) : (
            filteredCards.map((card, idx) => {
              const id = card.cardId || card.noteId || idx;
              const isFlipped = flippedCards[id];
              const status = card.status || 'Learning';

              return (
                <div
                  key={id}
                  onClick={() => toggleFlip(id)}
                  className="p-4 rounded-xl bg-[#0f172a] hover:bg-[#162035] border border-[#243049] cursor-pointer transition-all space-y-3 group select-none shadow-sm"
                >
                  <div className="flex items-center justify-between gap-3 text-[11px]">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-md font-bold text-[10px] uppercase tracking-wider ${
                        status === 'Mastered'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : status === 'Struggling'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}>
                        {status}
                      </span>
                      {card.interval !== undefined && (
                        <span className="text-slate-400">
                          Interval: <strong className="text-slate-200">{card.interval}d</strong>
                        </span>
                      )}
                      {card.reps !== undefined && (
                        <span className="text-slate-400">
                          Reps: <strong className="text-slate-200">{card.reps}</strong>
                        </span>
                      )}
                      {card.lapses !== undefined && card.lapses > 0 && (
                        <span className="text-rose-400">
                          Lapses: <strong>{card.lapses}</strong>
                        </span>
                      )}
                    </div>

                    <span className="text-slate-500 group-hover:text-indigo-400 text-[10px] transition-colors">
                      {isFlipped ? 'Click to hide back' : 'Click to flip →'}
                    </span>
                  </div>

                  {/* Front */}
                  <div className="text-sm font-semibold text-white leading-relaxed">
                    <div dangerouslySetInnerHTML={{ __html: card.front }} />
                  </div>

                  {/* Back (Revealed) */}
                  {isFlipped && (
                    <div className="pt-3 border-t border-[#243049] text-xs sm:text-sm text-emerald-300/90 leading-relaxed font-normal animate-fade-in bg-emerald-950/20 -mx-4 -mb-4 p-4 rounded-b-xl border-t border-emerald-500/20">
                      <div dangerouslySetInnerHTML={{ __html: card.back }} />
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#0f172a] border-t border-[#243049] flex items-center justify-between text-xs text-slate-400">
          <span>Showing {filteredCards.length} of {total} cards</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#1c263d] hover:bg-[#25324f] text-white font-medium transition-all cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
