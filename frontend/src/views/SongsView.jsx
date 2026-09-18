import React, { useState, useEffect } from 'react';
import { Music, ArrowLeft, ExternalLink, Play, Video, Sparkles } from 'lucide-react';
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
  const [playerTab, setPlayerTab] = useState('youtube');
  const [activeModalLine, setActiveModalLine] = useState(null);

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

  useEffect(() => {
    if (!activeSongSlug) return;
    setLoadingDetail(true);
    getSong(activeSongSlug)
      .then((data) => {
        setSongDetail(data);
        if (data.youtube_url) {
          setPlayerTab('youtube');
        } else if (data.spotify_url) {
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
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#243049]">
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

            <div className="flex items-center gap-3">
              {songDetail.youtube_url && (
                <a
                  href={songDetail.youtube_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/30 text-rose-300 text-xs font-medium transition-all"
                >
                  <Video size={13} />
                  <span>YouTube</span>
                  <ExternalLink size={11} />
                </a>
              )}
              {songDetail.spotify_url && (
                <a
                  href={songDetail.spotify_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-300 text-xs font-medium transition-all"
                >
                  <Play size={13} fill="currentColor" />
                  <span>Spotify</span>
                  <ExternalLink size={11} />
                </a>
              )}
            </div>
          </div>

          {/* Universal Embedded Media Player */}
          <div className="bg-[#151d2f] rounded-2xl border border-[#243049] p-4 sm:p-6 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#243049]/70 pb-3">
              <div className="flex items-center gap-2">
                <Music size={18} className="text-purple-400" />
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Universal Media Player
                </h2>
              </div>

              {/* Player Switcher Tabs */}
              <div className="flex items-center gap-2 bg-[#0f172a] p-1 rounded-xl border border-[#243049] self-start sm:self-auto">
                {songDetail.youtube_url && (
                  <button
                    onClick={() => setPlayerTab('youtube')}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      playerTab === 'youtube'
                        ? 'bg-rose-600 text-white shadow-md'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Video size={13} />
                    <span>YouTube Video</span>
                  </button>
                )}
                {songDetail.spotify_url && (
                  <button
                    onClick={() => setPlayerTab('spotify')}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      playerTab === 'spotify'
                        ? 'bg-emerald-600 text-white shadow-md'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Play size={13} fill="currentColor" />
                    <span>Spotify Audio</span>
                  </button>
                )}
              </div>
            </div>

            {/* Embedded Player Body */}
            {playerTab === 'youtube' && youtubeEmbedUrl && (
              <div className="w-full aspect-video rounded-xl overflow-hidden bg-black shadow-inner border border-[#243049]/80">
                <iframe
                  src={youtubeEmbedUrl}
                  title={`${songDetail.title} YouTube player`}
                  className="w-full h-full border-0"
                  allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            )}

            {playerTab === 'spotify' && spotifyEmbedUrl && (
              <div className="w-full rounded-xl overflow-hidden shadow-inner bg-[#121212] border border-[#243049]/80">
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
            )}

            {!songDetail.youtube_url && !songDetail.spotify_url && (
              <div className="p-6 text-center text-slate-400 text-xs bg-[#0f172a]/60 rounded-xl border border-[#243049]/50">
                No embedded audio or video player available for this track.
              </div>
            )}
          </div>

          {/* Song Header Info */}
          <div className="bg-[#151d2f] rounded-2xl border border-[#243049] p-6 sm:p-8 space-y-2 shadow-lg">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-bold uppercase tracking-wider">
              <Sparkles size={12} />
              <span>AZLyrics / Genius Clean View</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {songDetail.title}
            </h1>
            <p className="text-xs text-slate-400">
              Hover over or tap any lyric line to reveal its word-by-word gloss, literal translation, and natural English meaning.
            </p>
          </div>

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
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {songs.map((song) => (
                <div
                  key={song.id}
                  onClick={() => setActiveSongSlug(song.slug)}
                  className="group rounded-2xl bg-[#151d2f] border border-[#243049] hover:border-purple-500/50 p-6 sm:p-7 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-black/40 cursor-pointer flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 border border-purple-500/30 flex items-center justify-center text-lg">
                        🎵
                      </div>
                      <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded bg-[#0f172a] text-purple-300 border border-[#243049]">
                        4-Layer Breakdown
                      </span>
                    </div>

                    <h3 className="text-xl font-bold text-white group-hover:text-purple-400 transition-colors">
                      {song.title}
                    </h3>
                    <p className="text-xs text-slate-400">
                      Full lyric analysis, word glosses, and idiomatic translations.
                    </p>
                  </div>

                  <div className="pt-6 mt-6 border-t border-[#243049]/60 flex items-center justify-between text-xs font-semibold text-purple-400 group-hover:translate-x-1 transition-transform">
                    <span>Explore Breakdown</span>
                    <span>→</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
