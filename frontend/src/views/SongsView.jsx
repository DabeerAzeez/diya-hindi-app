import React, { useState, useEffect } from 'react';
import { Music, ArrowLeft, ExternalLink, Play, Video, Sparkles, Clock } from 'lucide-react';
import { getSongs, getSong } from '../services/api';

function getYouTubeEmbedUrl(url) {
  if (!url) return null;
  try {
    if (url.includes('/embed/')) return url;
    if (url.includes('youtu.be/')) {
      const id = url.split('youtu.be/')[1]?.split(/[?&]/)[0];
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
    if (url.includes('watch')) {
      const urlObj = new URL(url);
      const id = urlObj.searchParams.get('v');
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
  } catch {
    const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
    return match ? `https://www.youtube.com/embed/${match[1]}` : null;
  }
  return null;
}

function getSpotifyEmbedUrl(url) {
  if (!url) return null;
  try {
    if (url.includes('/embed/')) return url;
    if (url.includes('open.spotify.com/track/')) {
      const trackId = url.split('open.spotify.com/track/')[1]?.split(/[?&]/)[0];
      return trackId ? `https://open.spotify.com/embed/track/${trackId}?utm_source=generator&theme=0` : null;
    }
  } catch {
    const match = url.match(/track\/([a-zA-Z0-9]+)/);
    return match ? `https://open.spotify.com/embed/track/${match[1]}?utm_source=generator&theme=0` : null;
  }
  return null;
}

function parseDetails(details = []) {
  let gloss = '';
  let literal = '';
  let meaning = '';

  if (Array.isArray(details)) {
    details.forEach((det) => {
      if (!det || typeof det !== 'string') return;
      const lower = det.toLowerCase();
      if (lower.includes('word-by-word') || lower.includes('gloss')) {
        gloss = det.replace(/^.*?:\s*/i, '').replace(/`/g, '').trim();
      } else if (lower.includes('literal')) {
        literal = det.replace(/^.*?:\s*/i, '').replace(/^["']|["']$/g, '').replace(/`/g, '').trim();
      } else if (lower.includes('translation') || lower.includes('meaning')) {
        meaning = det.replace(/^.*?:\s*/i, '').replace(/^["']|["']$/g, '').replace(/`/g, '').trim();
      } else if (!meaning && det.trim()) {
        meaning = det.trim();
      }
    });
  }

  return { gloss, literal, meaning };
}

function cleanLineText(text = '') {
  if (!text) return '';
  return text.replace(/^\*\*|\*\*$/g, '').replace(/^["']|["']$/g, '').trim();
}

export default function SongsView() {
  const [songs, setSongs] = useState([]);
  const [activeSongSlug, setActiveSongSlug] = useState(null);
  const [songDetail, setSongDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [playerTab, setPlayerTab] = useState('spotify');
  const [activeModalLine, setActiveModalLine] = useState(null);
  const [dynamicCovers, setDynamicCovers] = useState({});

  // Anki Card Modal State
  const [ankiModalOpen, setAnkiModalOpen] = useState(false);
  const [ankiForm, setAnkiForm] = useState({ front: '', back: '', lesson: '' });
  const [savingAnki, setSavingAnki] = useState(false);
  const [ankiStatus, setAnkiStatus] = useState(null);

  useEffect(() => {
    getSongs()
      .then((data) => {
        setSongs(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching songs:', err);
        setLoading(false);
      });
  }, []);

  // Dynamically fetch Spotify cover art thumbnail via public oEmbed API if cover_art is missing
  useEffect(() => {
    if (!songs || songs.length === 0) return;
    songs.forEach((song) => {
      if (!song.cover_art && song.spotify_url && !dynamicCovers[song.slug]) {
        fetch(`https://open.spotify.com/oembed?url=${encodeURIComponent(song.spotify_url)}`)
          .then((res) => {
            if (!res.ok) throw new Error('oEmbed error');
            return res.json();
          })
          .then((data) => {
            if (data.thumbnail_url) {
              setDynamicCovers((prev) => ({ ...prev, [song.slug]: data.thumbnail_url }));
            }
          })
          .catch(() => {});
      }
    });
  }, [songs, dynamicCovers]);

  useEffect(() => {
    if (!activeSongSlug) return;
    setLoadingDetail(true);
    getSong(activeSongSlug)
      .then((data) => {
        setSongDetail(data);
        if (data.spotify_url) {
          setPlayerTab('spotify');
        } else {
          setPlayerTab(null);
        }
        setLoadingDetail(false);
      })
      .catch((err) => {
        console.error('Error fetching song detail:', err);
        setLoadingDetail(false);
      });
  }, [activeSongSlug]);

  const handleOpenAnkiModal = (data) => {
    const front = data.meaning || data.literal || data.line;
    const backLines = [];
    backLines.push(`<b>${data.line}</b>`);
    if (data.gloss) {
      backLines.push(`<small style="color: #60a5fa;">${data.gloss}</small>`);
    }
    if (data.literal) {
      backLines.push(`<small style="color: #94a3b8;"><i>Literal: "${data.literal}"</i></small>`);
    }
    if (songDetail?.title) {
      backLines.push(`<small style="color: #c084fc;"><b>🎵 Song:</b> ${songDetail.title}</small>`);
    }
    const back = backLines.join('<br>');

    setAnkiForm({
      front,
      back,
      lesson: songDetail?.slug || 'songs',
    });
    setAnkiStatus(null);
    setAnkiModalOpen(true);
  };

  const handleSaveAnkiCard = (e) => {
    e.preventDefault();
    setSavingAnki(true);
    setAnkiStatus(null);

    fetch('/api/anki/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        front: ankiForm.front,
        back: ankiForm.back,
        lesson: ankiForm.lesson || songDetail?.slug || 'songs',
      }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('API unavailable');
        return res.json();
      })
      .then((data) => {
        setSavingAnki(false);
        if (data.success) {
          setAnkiStatus({
            type: 'success',
            message: data.queued ? 'Card queued for offline Anki sync!' : 'Card successfully added to Anki deck!',
          });
          setTimeout(() => {
            setAnkiModalOpen(false);
            setAnkiStatus(null);
          }, 1400);
        } else {
          setAnkiStatus({
            type: 'error',
            message: data.error || 'Failed to add card to Anki.',
          });
        }
      })
      .catch(() => {
        try {
          const raw = localStorage.getItem('diya_cloud_anki_queue') || '[]';
          const queue = JSON.parse(raw);
          queue.push({
            front: ankiForm.front,
            back: ankiForm.back,
            lesson: ankiForm.lesson || songDetail?.slug || 'songs',
            timestamp: new Date().toISOString()
          });
          localStorage.setItem('diya_cloud_anki_queue', JSON.stringify(queue));
          setSavingAnki(false);
          setAnkiStatus({
            type: 'success',
            message: 'Saved to local browser queue! (Desktop syncs when run locally)',
          });
          setTimeout(() => {
            setAnkiModalOpen(false);
            setAnkiStatus(null);
          }, 1800);
        } catch (_) {
          setSavingAnki(false);
          setAnkiStatus({
            type: 'error',
            message: 'Network error communicating with Anki bridge.',
          });
        }
      });
  };

  const youtubeEmbedUrl = getYouTubeEmbedUrl(songDetail?.youtube_url);
  const spotifyEmbedUrl = getSpotifyEmbedUrl(songDetail?.spotify_url);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* If viewing a song breakdown */}
      {loadingDetail ? (
        <div className="p-16 text-center text-slate-400 text-sm animate-pulse">
          Loading song breakdown...
        </div>
      ) : songDetail ? (
        <div className="space-y-8">
          {/* Top Bar Navigation */}
          <div className="flex items-center justify-between gap-4 pb-6 border-b border-[#243049]">
            <button
              onClick={() => {
                setActiveSongSlug(null);
                setSongDetail(null);
              }}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#151d2f] hover:bg-[#1c263d] border border-[#243049] text-sm text-slate-300 hover:text-white transition-all w-fit shadow-sm"
            >
              <ArrowLeft size={16} />
              <span>Back to Song Library</span>
            </button>
          </div>

          {/* 1. Song Title Block - Larger typography, clean and prominent without redundant details */}
          <div className="pt-2 pb-1">
            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-tight">
              {songDetail.title}
            </h1>
          </div>

          {/* 2. Embedded Media Player - Clean Spotify Audio Player (Universal Media Player; aspect-video container) */}
          {spotifyEmbedUrl ? (
            <div className="w-full rounded-2xl overflow-hidden shadow-2xl bg-[#121212] border border-[#243049]/80">
              <iframe
                src={spotifyEmbedUrl}
                title={`${songDetail.title} Spotify player`}
                width="100%"
                height="152"
                className="w-full border-0"
                allow="encrypted-media; fullscreen; picture-in-picture"
                loading="lazy"
              />
            </div>
          ) : (
            <div className="p-6 text-center text-slate-400 text-xs bg-[#151d2f] rounded-2xl border border-[#243049]/50 shadow-lg">
              No embedded Spotify audio player available for this track.
            </div>
          )}

          {/* AZLyrics / Genius-Style Clean Lyrics View */}
          <div className="max-w-3xl mx-auto bg-[#101726] border border-[#243049] rounded-2xl p-6 sm:p-10 shadow-2xl space-y-8">
            {songDetail.verses?.map((verse, vIdx) => (
              <div key={vIdx} className="space-y-3">
                {/* Section Header */}
                <div className="text-xs uppercase tracking-widest font-bold text-purple-400 pb-1.5 border-b border-[#243049]/60">
                  [{verse.title ? verse.title.replace(/[\][]/g, '') : `Section ${vIdx + 1}`}]
                </div>

                {/* Plain text lyric lines with hover modal */}
                <div className="space-y-1 font-sans">
                  {verse.lines?.map((lineObj, lIdx) => {
                    const lineKey = `${vIdx}-${lIdx}`;
                    const cleanLine = cleanLineText(lineObj.line);
                    const parsed = parseDetails(lineObj.details);
                    const isHovered = activeModalLine === lineKey;

                    return (
                      <div
                        key={lIdx}
                        className="relative group py-1.5 px-3 rounded-lg hover:bg-[#1a233a] transition-all cursor-pointer"
                        onMouseEnter={() => setActiveModalLine(lineKey)}
                        onMouseLeave={() => setActiveModalLine(null)}
                        onClick={() => setActiveModalLine(isHovered ? null : lineKey)}
                      >
                        {/* Plain text line */}
                        <div className="text-base sm:text-lg leading-relaxed text-slate-200 group-hover:text-amber-300 transition-colors">
                          {cleanLine}
                        </div>

                        {/* Floating Hover Modal on Lyric Line */}
                        {isHovered && (
                          <div
                            className="absolute left-0 top-full mt-2 w-full sm:w-[500px] max-w-[92vw] z-30 bg-[#0f172a] border border-purple-500/40 rounded-xl p-4 shadow-2xl space-y-3 backdrop-blur-xl animate-fade-in"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <div className="flex items-center justify-between pb-2 border-b border-[#243049]">
                              <span className="text-[11px] uppercase tracking-wider font-bold text-purple-400">
                                Linguistic Breakdown
                              </span>
                              <button
                                onClick={() => setActiveModalLine(null)}
                                className="text-slate-400 hover:text-white text-xs p-1"
                              >
                                ✕
                              </button>
                            </div>

                            {parsed.gloss ? (
                              <div className="text-xs">
                                <span className="font-semibold text-slate-400">Word-by-Word Gloss: </span>
                                <span className="text-cyan-300 font-mono text-[11px]">{parsed.gloss}</span>
                              </div>
                            ) : null}

                            {parsed.literal ? (
                              <div className="text-xs text-slate-300 italic">
                                <span className="font-semibold not-italic text-slate-400">Literal Translation: </span>
                                "{parsed.literal}"
                              </div>
                            ) : null}

                            {parsed.meaning ? (
                              <div className="text-xs text-emerald-300 font-medium bg-emerald-950/40 border border-emerald-500/20 rounded-lg p-2.5">
                                <span className="font-semibold text-emerald-400 text-xs block mb-0.5">Meaning: </span>
                                "{parsed.meaning}"
                              </div>
                            ) : null}

                            {!parsed.gloss && !parsed.literal && !parsed.meaning && (
                              <div className="text-xs text-slate-400 italic">
                                No additional linguistic details for this line.
                              </div>
                            )}

                            {/* Add to Anki Button */}
                            <div className="pt-2 border-t border-[#243049]">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleOpenAnkiModal({
                                    line: cleanLine,
                                    gloss: parsed.gloss,
                                    literal: parsed.literal,
                                    meaning: parsed.meaning,
                                  });
                                }}
                                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md transition-all"
                              >
                                <span>🎴 Add to Anki</span>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* Add to Anki Modal Dialog */}
          {ankiModalOpen && (
            <div
              className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
              onClick={() => setAnkiModalOpen(false)}
            >
              <div
                className="bg-[#151d2f] border border-[#243049] rounded-2xl p-6 sm:p-8 max-w-lg w-full shadow-2xl space-y-5"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between border-b border-[#243049] pb-4">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>🎴 Add Lyric Card to Anki</span>
                  </h3>
                  <button
                    onClick={() => setAnkiModalOpen(false)}
                    className="text-slate-400 hover:text-white text-sm p-1 rounded-lg"
                  >
                    ✕
                  </button>
                </div>

                {ankiStatus && (
                  <div
                    className={`p-3 rounded-xl text-xs font-medium ${
                      ankiStatus.type === 'success'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}
                  >
                    {ankiStatus.message}
                  </div>
                )}

                <form onSubmit={handleSaveAnkiCard} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                      Front (Question / Prompt)
                    </label>
                    <textarea
                      value={ankiForm.front}
                      onChange={(e) => setAnkiForm((prev) => ({ ...prev, front: e.target.value }))}
                      rows={2}
                      className="w-full rounded-xl bg-[#0f172a] border border-[#243049] px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors resize-none"
                      placeholder="English meaning or prompt..."
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                      Back (Answer / Hindi Target)
                    </label>
                    <textarea
                      value={ankiForm.back}
                      onChange={(e) => setAnkiForm((prev) => ({ ...prev, back: e.target.value }))}
                      rows={5}
                      className="w-full rounded-xl bg-[#0f172a] border border-[#243049] px-3.5 py-2.5 text-xs text-white font-mono focus:outline-none focus:border-purple-500 transition-colors"
                      placeholder="Hindi lyric and details..."
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                      Lesson / Tag
                    </label>
                    <input
                      type="text"
                      value={ankiForm.lesson}
                      onChange={(e) => setAnkiForm((prev) => ({ ...prev, lesson: e.target.value }))}
                      className="w-full rounded-xl bg-[#0f172a] border border-[#243049] px-3.5 py-2 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
                      placeholder="song_jeena_jeena"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setAnkiModalOpen(false)}
                      className="px-4 py-2 rounded-xl bg-[#1a233a] hover:bg-[#243049] text-xs font-medium text-slate-300 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={savingAnki}
                      className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-xs font-bold text-white shadow-lg transition-all"
                    >
                      {savingAnki ? 'Saving...' : 'Add to Anki'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Song Library Catalog */
        <div className="space-y-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-3">
              <span>🎵 Bollywood & Hindi Song Lyrics</span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                {songs.length} Saved
              </span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Learn Hindi naturally through Bollywood music with line-by-line 4-layer linguistic deconstructions.
            </p>
          </div>

          {loading ? (
            <div className="p-12 text-center text-slate-400 text-sm">Loading songs...</div>
          ) : songs.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-sm">No songs found.</div>
          ) : (
            <div className="bg-[#151d2f] rounded-2xl border border-[#243049] overflow-hidden shadow-2xl">
              {/* Spotify Playlist Column Headers (3 columns: Title, Album, Duration) */}
              <div className="grid grid-cols-12 gap-4 px-4 sm:px-6 py-3 border-b border-[#243049] text-[11px] font-bold uppercase tracking-wider text-slate-400 select-none items-center">
                <div className="col-span-7 sm:col-span-6 flex items-center gap-3">
                  <span className="w-6 text-center">#</span>
                  <span>Title</span>
                </div>
                <div className="col-span-3 sm:col-span-4">Album</div>
                <div className="col-span-2 text-right pr-2 sm:pr-4 flex items-center justify-end">
                  <Clock size={15} className="text-slate-400" />
                </div>
              </div>

              {/* Playlist Tracks List (Full Width Rows - 3 Columns) */}
              <div className="divide-y divide-[#243049]/40">
                {songs.map((song, idx) => {
                  const coverUrl = song.cover_art || dynamicCovers[song.slug];
                  return (
                    <div
                      key={song.id || song.slug}
                      onClick={() => setActiveSongSlug(song.slug)}
                      className="group grid grid-cols-12 gap-4 px-4 sm:px-6 py-3.5 items-center hover:bg-[#1b253b] transition-all cursor-pointer select-none"
                    >
                      {/* Column 1: # Index / Play Indicator + Album Cover Art + Title & Artist */}
                      <div className="col-span-7 sm:col-span-6 flex items-center gap-3.5 min-w-0">
                        <div className="w-6 shrink-0 text-center flex items-center justify-center">
                          <span className="text-xs font-semibold text-slate-400 group-hover:hidden">
                            {idx + 1}
                          </span>
                          <Play
                            size={14}
                            className="hidden group-hover:block text-emerald-400"
                            fill="currentColor"
                          />
                        </div>

                        {coverUrl ? (
                          <img
                            src={coverUrl}
                            alt={song.title}
                            className="w-12 h-12 rounded-lg object-cover shadow-md border border-[#243049]/80 shrink-0 group-hover:scale-105 transition-transform"
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        ) : (
                          <div className="w-12 h-12 rounded-lg bg-[#0f172a] border border-[#243049] flex items-center justify-center text-lg shrink-0 group-hover:border-emerald-500/50">
                            🎵
                          </div>
                        )}

                        <div className="min-w-0 pr-2">
                          <h3 className="text-sm sm:text-base font-bold text-white group-hover:text-emerald-400 transition-colors truncate">
                            {song.title}
                          </h3>
                          <p className="text-xs text-slate-400 truncate">
                            {song.artist || 'Bollywood Classic'}
                          </p>
                        </div>
                      </div>

                      {/* Column 2: Movie / Soundtrack */}
                      <div className="col-span-3 sm:col-span-4 text-xs text-slate-300 font-medium truncate">
                        {song.movie || '—'}
                      </div>

                      {/* Column 3: Duration */}
                      <div className="col-span-2 text-right pr-2 sm:pr-4 text-xs font-mono text-slate-400 group-hover:text-slate-200">
                        {song.duration || '—'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
