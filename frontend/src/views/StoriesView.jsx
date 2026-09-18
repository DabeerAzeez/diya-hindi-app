import React, { useState, useEffect } from 'react';
import { Clock, ExternalLink, Sparkles } from 'lucide-react';
import { getStories, getStoryUrl, resolvePath } from '../services/api';

// Hardcover jewel-tone color palettes for deterministic fallback
const JEWEL_PALETTES = [
  { bg: '#1e3a8a', border: '#3b82f6', foil: '#93c5fd', name: 'Royal Sapphire' },
  { bg: '#14532d', border: '#22c55e', foil: '#86efac', name: 'Forest Emerald' },
  { bg: '#581c87', border: '#a855f7', foil: '#e9d5ff', name: 'Imperial Plum' },
  { bg: '#831843', border: '#f43f5e', foil: '#fecdd3', name: 'Deep Burgundy' },
  { bg: '#7c2d12', border: '#ea580c', foil: '#fed7aa', name: 'Warm Terracotta' },
  { bg: '#0f766e', border: '#14b8a6', foil: '#99f6e4', name: 'Deep Sea Teal' },
  { bg: '#312e81', border: '#6366f1', foil: '#c7d2fe', name: 'Midnight Indigo' },
  { bg: '#1e293b', border: '#64748b', foil: '#e2e8f0', name: 'Slate Hardcover' },
];

function getBookCoverTheme(id = '') {
  let hash = 0;
  const str = String(id || 'story');
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) & 0xffffffff;
  }
  return JEWEL_PALETTES[Math.abs(hash) % JEWEL_PALETTES.length];
}

export default function StoriesView() {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [imageErrors, setImageErrors] = useState({});

  useEffect(() => {
    // Direct API stories loading: fetch('/api/stories') via unified getStories service
    getStories()
      .then((data) => {
        setStories(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading stories:', err);
        setLoading(false);
      });
  }, []);

  const handleImageError = (id) => {
    setImageErrors((prev) => ({ ...prev, [id]: true }));
  };

  const handleOpenStory = (story) => {
    const url = getStoryUrl(story);
    // Opens full-screen reader in separate tab: window.open('/api/stories/' + story.id + '/raw', '_blank')
    window.open(url || `/api/stories/${story.id}/raw`, '_blank');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Page Header */}
      <div className="mb-10">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <span>📚 Bilingual Stories</span>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            {stories.length} Available
          </span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Immersive Hinglish stories with synchronized sentence highlighting, hover tooltips, and audio.
        </p>
      </div>

      {loading ? (
        <div className="p-16 text-center text-slate-400 text-sm">Loading stories...</div>
      ) : stories.length === 0 ? (
        <div className="p-16 text-center text-slate-500 text-sm">No stories available.</div>
      ) : (
        /* Library Bookshelf Section */
        <div className="space-y-12 bookshelf-container">
          <div className="bg-[#0f172a]/70 border border-[#1e293b] rounded-3xl p-6 sm:p-10 shadow-2xl relative overflow-hidden backdrop-blur-sm">
            {/* Standing Books Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 sm:gap-10 items-end px-2 pt-4 pb-2">
              {stories.map((story) => {
                const palette = getBookCoverTheme(story.id);
                const hasCover = story.cover_image && !imageErrors[story.id];

                return (
                  <div
                    key={story.id}
                    className="flex flex-col items-center text-center group"
                  >
                    {/* Standing Vertical Hardcover Book with 3D hover lift */}
                    <div
                      onClick={() => handleOpenStory(story)}
                      className="relative w-48 sm:w-52 h-72 sm:h-80 aspect-[3/4] rounded-r-2xl rounded-l-sm cursor-pointer select-none transition-all duration-300 ease-out hover:-translate-y-4 hover:scale-[1.03] shadow-[0_16px_28px_rgba(0,0,0,0.75)] hover:shadow-[0_24px_40px_rgba(0,0,0,0.9)] border-l-[8px] border-black/40 overflow-hidden flex flex-col justify-between"
                      style={{
                        backgroundColor: hasCover ? '#0b0f19' : palette.bg,
                      }}
                      title={`Open "${story.title}" in full-screen reader`}
                    >
                      {/* Spine 3D groove shadow */}
                      <div className="absolute inset-y-0 left-0 w-4 bg-gradient-to-r from-black/60 via-black/20 to-transparent pointer-events-none z-20" />
                      {/* Right edge paper shine */}
                      <div className="absolute inset-y-0 right-0 w-2 bg-gradient-to-l from-white/15 to-transparent pointer-events-none z-20" />

                      {hasCover ? (
                        /* AI Generated Cover Image */
                        <div className="w-full h-full relative overflow-hidden">
                          <img
                            src={story.cover_image?.startsWith('/api/stories/assets/') ? resolvePath(story.cover_image.replace('/api/stories/', 'data/stories/')) : story.cover_image}
                            alt={story.title || 'Story Cover'}
                            onError={() => handleImageError(story.id)}
                            className="w-full h-full object-cover rounded-r-2xl rounded-l-sm group-hover:scale-105 transition-transform duration-500"
                          />
                          {/* Dark vignette gradient overlay */}
                          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-black/40 pointer-events-none" />

                          {/* Top Level Pill */}
                          <div className="absolute top-3 right-3 z-10">
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-black/60 backdrop-blur-md text-cyan-300 border border-cyan-400/30 shadow-sm">
                              {story.level || 'A1'}
                            </span>
                          </div>

                          {/* Bottom Title on Image */}
                          <div className="absolute inset-x-0 bottom-0 p-4 z-10 text-left">
                            <div className="text-[11px] font-medium text-amber-300 flex items-center gap-1 mb-1">
                              <Sparkles size={11} />
                              <span>Diya Reader</span>
                            </div>
                            <h3 className="font-serif font-bold text-white text-base sm:text-lg leading-snug line-clamp-3 drop-shadow-md">
                              {story.title || 'Untitled Story'}
                            </h3>
                          </div>
                        </div>
                      ) : (
                        /* Deterministic Solid Jewel-Tone Fallback Cover */
                        <div
                          className="w-full h-full p-4 flex flex-col justify-between relative fallback-cover"
                          style={{ backgroundColor: palette.bg }}
                        >
                          {/* Inset Gold Foil Borders */}
                          <div className="absolute inset-2 border border-white/20 rounded-r-xl rounded-l-xs pointer-events-none" />
                          <div
                            className="absolute inset-3 border rounded-r-lg rounded-l-xs pointer-events-none opacity-60"
                            style={{ borderColor: palette.foil }}
                          />

                          {/* Top Cover Header: Level & Hindi Accent */}
                          <div className="relative z-10 flex items-center justify-between pt-1 px-1">
                            <span
                              className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-black/40 border shadow-sm"
                              style={{ color: palette.foil, borderColor: `${palette.foil}40` }}
                            >
                              {story.level || 'A1'}
                            </span>
                            <span className="text-[11px] tracking-widest text-amber-300/80">
                              ✦ ✦ ✦
                            </span>
                          </div>

                          {/* Middle: Prominent White Title in Clean Serif Typography */}
                          <div className="relative z-10 py-4 px-2 my-auto text-center">
                            <h3 className="font-serif font-bold text-white text-base sm:text-lg leading-snug line-clamp-3 drop-shadow-lg">
                              {story.title || 'Untitled Story'}
                            </h3>
                            <p
                              className="text-[11px] font-medium mt-2 tracking-wide uppercase"
                              style={{ color: palette.foil }}
                            >
                              Diya • Hindi Reader
                            </p>
                          </div>

                          {/* Bottom Cover Footer: Reading time */}
                          <div className="relative z-10 pb-1 text-center">
                            <div className="text-[11px] text-white/80 font-medium inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-black/40 border border-white/10">
                              <Clock size={11} />
                              <span>{story.readingTime || '10 min'}</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Hover Action Lift Overlay */}
                      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center p-3 rounded-r-2xl rounded-l-sm z-30">
                        <span className="px-3.5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-xl flex items-center gap-2 transform translate-y-2 group-hover:translate-y-0 transition-transform">
                          <span>Read Story</span>
                          <ExternalLink size={13} />
                        </span>
                      </div>
                    </div>

                    {/* Book Metadata & Title Link Below Cover */}
                    <div className="mt-4 w-full px-1 flex flex-col items-center">
                      <a
                        href={`/api/stories/${story.id}/raw`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => {
                          e.preventDefault();
                          handleOpenStory(story);
                        }}
                        className="font-semibold text-sm text-slate-200 hover:text-cyan-400 transition-colors line-clamp-1 group-hover:underline"
                        title={story.title}
                      >
                        {story.title}
                      </a>

                      <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-400">
                        <span className="font-medium text-cyan-400">{story.level || 'A1'}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock size={12} />
                          {story.readingTime || '10 min'}
                        </span>
                      </div>

                      {story.topics && story.topics.length > 0 && (
                        <div className="flex flex-wrap justify-center gap-1 mt-2">
                          {story.topics.slice(0, 2).map((topic, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-[#1e293b] text-slate-300 border border-[#334155]/60"
                            >
                              #{topic}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Wooden / Metallic Dark Shelf Ledge */}
            <div className="relative w-full mt-4">
              {/* Top Highlight line */}
              <div className="w-full h-[2px] bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent" />
              {/* Solid shelf beam */}
              <div className="w-full h-6 rounded-b-md bg-gradient-to-r from-[#172033] via-[#28354f] to-[#172033] border-t border-[#3b82f6]/30 shadow-[0_16px_32px_rgba(0,0,0,0.85)] flex items-center justify-between px-6">
                <div className="w-full h-[1px] bg-white/10" />
              </div>
              {/* Cast shadow underneath shelf */}
              <div className="w-full h-4 bg-gradient-to-b from-black/80 to-transparent pointer-events-none" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
