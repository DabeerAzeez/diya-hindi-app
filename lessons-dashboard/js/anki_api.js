/**
 * AnkiConnect Client & Data Bridge for lessons-dashboard
 * Attempts live fetch from AnkiConnect (http://127.0.0.1:8765).
 * Gracefully falls back to local data/deck_snapshot.json.
 */

const ANKI_URL = "http://127.0.0.1:8765";
const DEFAULT_DECK = "Hindi";

export async function checkAnkiLiveConnection() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1200);
    const resp = await fetch(ANKI_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "version", version: 6 }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    if (!resp.ok) return false;
    const data = await resp.json();
    return data && !data.error && data.result >= 6;
  } catch (err) {
    return false;
  }
}

export async function fetchLiveAnkiCards() {
  try {
    // 1. Find card IDs
    const findResp = await fetch(ANKI_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "findCards",
        version: 6,
        params: { query: `deck:"${DEFAULT_DECK}"` }
      })
    });
    const findData = await findResp.json();
    if (findData.error || !findData.result) throw new Error(findData.error || "No cards found");

    const cardIds = findData.result;
    if (cardIds.length === 0) return [];

    // 2. Fetch cardsInfo in chunks
    const chunkSize = 50;
    const cards = [];
    for (let i = 0; i < cardIds.length; i += chunkSize) {
      const chunk = cardIds.slice(i, i + chunkSize);
      const cResp = await fetch(ANKI_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "cardsInfo", version: 6, params: { cards: chunk } })
      });
      const cData = await cResp.json();
      if (cData.result) cards.push(...cData.result);
    }

    // 3. Fetch notesInfo for tags in chunks
    const noteIds = Array.from(new Set(cards.map(c => c.note)));
    const notesMap = {};
    for (let i = 0; i < noteIds.length; i += chunkSize) {
      const nChunk = noteIds.slice(i, i + chunkSize);
      const nResp = await fetch(ANKI_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "notesInfo", version: 6, params: { notes: nChunk } })
      });
      const nData = await nResp.json();
      if (nData.result) {
        nData.result.forEach(n => {
          notesMap[n.noteId] = n.tags || [];
        });
      }
    }

    // 4. Map into standard schema
    const processed = cards.map(c => {
      const interval = c.interval || 0;
      const reps = c.reps || 0;
      const lapses = c.lapses || 0;
      const queue = c.queue || 0;
      const factor = c.factor || 2500;
      const tags = notesMap[c.note] || [];

      let status = "Learning";
      if (queue === 0 || reps === 0) {
        status = "Learning";
      } else if (queue === 1 || (lapses >= 2 && interval < 7) || (factor < 1700 && interval < 7)) {
        status = "Struggling";
      } else if (interval >= 14 && reps >= 3) {
        status = "Mastered";
      }

      const lessonTags = [];
      let isGeneral = false;
      tags.forEach(t => {
        if (t.startsWith("lesson::")) {
          const code = t.replace("lesson::", "");
          if (code === "general") isGeneral = true;
          else lessonTags.push(code);
        }
      });

      return {
        cardId: c.cardId,
        noteId: c.note,
        front: c.fields?.Front?.value || "",
        back: c.fields?.Back?.value || "",
        interval,
        reps,
        lapses,
        queue,
        factor,
        status,
        tags,
        lesson_codes: lessonTags,
        is_general: isGeneral
      };
    });

    return {
      synced_at: new Date().toISOString(),
      is_live: true,
      cards: processed
    };
  } catch (err) {
    console.warn("Live AnkiConnect fetch failed, falling back to cached snapshot:", err);
    return null;
  }
}

export async function loadDeckData() {
  const isLive = await checkAnkiLiveConnection();
  if (isLive) {
    const liveData = await fetchLiveAnkiCards();
    if (liveData && liveData.cards.length > 0) {
      return liveData;
    }
  }

  // Check if loaded via static script tag (works in file:/// mode)
  if (typeof window !== "undefined" && window.DECK_SNAPSHOT) {
    return {
      ...window.DECK_SNAPSHOT,
      is_live: false
    };
  }

  // Fallback to local snapshot via fetch
  const resp = await fetch("data/deck_snapshot.json");
  if (!resp.ok) {
    throw new Error(`Failed to load data/deck_snapshot.json (${resp.status})`);
  }
  const snapshot = await resp.json();
  return {
    ...snapshot,
    is_live: false
  };
}

export async function loadCurriculumData() {
  if (typeof window !== "undefined" && window.CURRICULUM_DATA) {
    return window.CURRICULUM_DATA;
  }
  const resp = await fetch("data/curriculum.json");
  if (!resp.ok) {
    throw new Error(`Failed to load data/curriculum.json (${resp.status})`);
  }
  return await resp.json();
}
