// Unified API Service for DIYA
// Automatically handles live local server (/api/*) and static cloud hosting (GitHub Pages / Vercel / Cloudflare)

const isLocal = typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// Resolve relative or base paths
const BASE_PATH = import.meta.env.BASE_URL || './';

export function resolvePath(subpath) {
  const cleanSub = subpath.startsWith('/') ? subpath.slice(1) : subpath;
  const base = BASE_PATH.endsWith('/') ? BASE_PATH : `${BASE_PATH}/`;
  return `${base}${cleanSub}`;
}

export async function getStatus() {
  if (isLocal) {
    try {
      const res = await fetch('/api/status');
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  return {
    app: 'DIYA Hindi Hub',
    version: '1.0.0',
    anki_connected: false,
    mode: 'cloud'
  };
}

export async function pingHeartbeat() {
  if (isLocal) {
    try {
      await fetch('/api/heartbeat');
    } catch (_) {}
  }
}

export async function getLessons() {
  if (isLocal) {
    try {
      const res = await fetch('/api/lessons');
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  const res = await fetch(resolvePath('data/lessons_index.json'));
  return await res.json();
}

export async function getLesson(slug) {
  if (isLocal) {
    try {
      const res = await fetch(`/api/lessons/${slug}`);
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  const res = await fetch(resolvePath(`data/lessons/${slug}.json`));
  return await res.json();
}

export async function getSongs() {
  if (isLocal) {
    try {
      const res = await fetch('/api/songs');
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  const res = await fetch(resolvePath('data/songs_index.json'));
  return await res.json();
}

export async function getSong(slug) {
  if (isLocal) {
    try {
      const res = await fetch(`/api/songs/${slug}`);
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  const res = await fetch(resolvePath(`data/songs/${slug}.json`));
  return await res.json();
}

export async function getStories() {
  if (isLocal) {
    try {
      const res = await fetch('/api/stories');
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  const res = await fetch(resolvePath('data/stories_index.json'));
  return await res.json();
}

export function getStoryUrl(story) {
  if (isLocal) {
    return `/api/stories/${story.id || story.filename}/raw`;
  }
  const filename = story.filename || `${story.id}.html`;
  return resolvePath(`data/stories/${filename}`);
}

export async function getAnkiCards() {
  if (isLocal) {
    try {
      const res = await fetch('/api/anki/cards');
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  // Cloud snapshot fallback
  try {
    const res = await fetch(resolvePath('data/deck_snapshot.json'));
    const data = await res.json();
    return {
      live: false,
      mode: 'cloud',
      synced_at: data.synced_at || null,
      stats: data.stats || {},
      cards: data.cards || []
    };
  } catch (err) {
    return {
      live: false,
      mode: 'cloud',
      stats: { total: 0, Mastered: 0, Learning: 0, Struggling: 0 },
      cards: []
    };
  }
}

export async function getProfile() {
  // Check localStorage for personal cloud notes first
  const localSaved = localStorage.getItem('diya_cloud_profile');
  if (localSaved && !isLocal) {
    try {
      return JSON.parse(localSaved);
    } catch (_) {}
  }

  if (isLocal) {
    try {
      const res = await fetch('/api/profile');
      if (res.ok) return await res.json();
    } catch (_) {}
  }

  const res = await fetch(resolvePath('data/profile.json'));
  return await res.json();
}

export async function saveProfile(profileData) {
  if (isLocal) {
    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData)
      });
      if (res.ok) return await res.json();
    } catch (_) {}
  }

  // Cloud fallback: save to browser localStorage
  localStorage.setItem('diya_cloud_profile', JSON.stringify(profileData));
  return { status: 'saved_locally', ...profileData };
}
