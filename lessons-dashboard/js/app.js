import { loadDeckData, loadCurriculumData, checkAnkiLiveConnection } from "./anki_api.js";

const MIN_CARDS_PER_LESSON = 5;
const MAX_STRUGGLING_ALLOWED = 2;
const MAX_LEARNING_ALLOWED = 6;

let state = {
  curriculum: [],
  cards: [],
  isLive: false,
  syncedAt: null,
  activeView: "overview", // "overview" | "lesson" | "general"
  activeLessonCode: null,
  cardFilter: "all",
  searchQuery: ""
};

// --- CORE GATING & STATUS LOGIC ---
function computeCurriculumState() {
  const lessonMap = {};
  state.curriculum.forEach(l => {
    lessonMap[l.code] = {
      ...l,
      cards: [],
      status: "Locked",
      masteredCount: 0,
      learningCount: 0,
      strugglingCount: 0
    };
  });

  // Group cards into lessons using primary ceiling lesson
  state.cards.forEach(card => {
    const primaryCode = card.primary_lesson || (card.lesson_codes && card.lesson_codes[0]);
    if (!primaryCode || primaryCode === "general" || card.is_general) {
      return; // pure general or sneak peek
    }
    if (lessonMap[primaryCode]) {
      lessonMap[primaryCode].cards.push(card);
    }
  });

  // Evaluate sequential progression gating
  let unlockedCodes = new Set();
  let strugglingCountSoFar = 0;
  let learningCountSoFar = 0;
  let incompleteCountSoFar = 0;

  for (let i = 0; i < state.curriculum.length; i++) {
    const lesson = state.curriculum[i];
    const code = lesson.code;
    const lData = lessonMap[code];
    const totalCards = lData.cards.length;

    // Evaluate card stats
    let m = 0, l = 0, s = 0;
    lData.cards.forEach(c => {
      if (c.status === "Mastered") m++;
      else if (c.status === "Learning") l++;
      else if (c.status === "Struggling") s++;
    });
    lData.masteredCount = m;
    lData.learningCount = l;
    lData.strugglingCount = s;

    // Special handling for A0-X
    if (code === "A0-X") {
      unlockedCodes.add(code);
      lData.status = "Reference";
      continue;
    }

    // STRICT NOTION CAP: A lesson is unlocked ONLY IF its Notion page has been created (is_completed)
    const isCompletedInNotion = !!lesson.is_completed;

    if (isCompletedInNotion) {
      unlockedCodes.add(code);

      const sRate = totalCards > 0 ? (s / totalCards) : 0;
      const mRate = totalCards > 0 ? (m / totalCards) : 0;

      // Determine lesson status
      if (totalCards < MIN_CARDS_PER_LESSON) {
        lData.status = "Needs Cards";
        incompleteCountSoFar++;
      } else if (sRate >= 0.25 && s >= 2) {
        lData.status = "Struggling";
        strugglingCountSoFar++;
      } else if (mRate >= 0.65 && sRate <= 0.20) {
        lData.status = "Mastered";
      } else {
        lData.status = "Learning";
        learningCountSoFar++;
      }
    } else {
      lData.status = "Locked";
    }
  }

  return {
    lessonMap,
    unlockedCodes,
    strugglingCountSoFar,
    learningCountSoFar,
    incompleteCountSoFar
  };
}

// --- RENDER FUNCTIONS ---
function renderHeader() {
  const syncDot = document.getElementById("sync-dot");
  const syncLabel = document.getElementById("sync-label");
  if (state.isLive) {
    syncDot.className = "sync-dot live";
    syncLabel.textContent = "Live AnkiConnect";
  } else {
    syncDot.className = "sync-dot";
    const dateStr = state.syncedAt ? new Date(state.syncedAt).toLocaleTimeString() : "Snapshot";
    syncLabel.textContent = `Cached Snapshot (${dateStr})`;
  }
}

function renderStats(curriculumState) {
  const totalCards = state.cards.length;
  let mastered = 0, learning = 0, struggling = 0;
  state.cards.forEach(c => {
    if (c.status === "Mastered") mastered++;
    else if (c.status === "Learning") learning++;
    else if (c.status === "Struggling") struggling++;
  });

  const mPct = totalCards > 0 ? Math.round((mastered / totalCards) * 100) : 0;
  const lPct = totalCards > 0 ? Math.round((learning / totalCards) * 100) : 0;
  const sPct = totalCards > 0 ? Math.round((struggling / totalCards) * 100) : 0;

  document.getElementById("stat-total-cards").textContent = totalCards;
  document.getElementById("stat-mastered").textContent = `${mastered} (${mPct}%)`;
  document.getElementById("stat-learning").textContent = `${learning} (${lPct}%)`;
  document.getElementById("stat-struggling").textContent = `${struggling} (${sPct}%)`;
}

function renderProgressionBanner(curriculumState) {
  const banner = document.getElementById("progression-banner");
  const icon = document.getElementById("banner-icon");
  const title = document.getElementById("banner-title");
  const desc = document.getElementById("banner-desc");

  const { lessonMap, strugglingCountSoFar, learningCountSoFar, incompleteCountSoFar } = curriculumState;

  // Find next locked lesson
  let nextLesson = null;
  for (const l of state.curriculum) {
    if (lessonMap[l.code].status === "Locked") {
      nextLesson = l;
      break;
    }
  }

  if (!nextLesson) {
    banner.className = "progression-banner ready";
    icon.textContent = "🎉";
    title.textContent = "All Curriculum Modules Completed in Notion!";
    desc.textContent = "You have completed all lessons across A0, A1, and A2 in Notion. Keep practicing in Anki to maintain Mastered status!";
    return;
  }

  const strugglingBlockers = [];
  const deficitLessons = [];
  state.curriculum.forEach(l => {
    const s = lessonMap[l.code].status;
    if (s === "Struggling") {
      strugglingBlockers.push(`${l.code} (${lessonMap[l.code].strugglingCount} failing cards)`);
    } else if (s === "Needs Cards" && l.is_completed) {
      deficitLessons.push(`${l.code} (${lessonMap[l.code].cards.length}/${MIN_CARDS_PER_LESSON})`);
    }
  });

  if (strugglingCountSoFar <= MAX_STRUGGLING_ALLOWED) {
    banner.className = "progression-banner ready";
    icon.textContent = "🚀";
    title.textContent = `Advisory: Ready to Advance to ${nextLesson.code}: ${nextLesson.title}`;
    let note = `Active prerequisite debt is within healthy targets (${strugglingCountSoFar}/${MAX_STRUGGLING_ALLOWED} Struggling allowed). You are conceptually ready to create and study Lesson ${nextLesson.code} in Notion whenever you choose!`;
    if (strugglingBlockers.length > 0) {
      note += ` (Recommended polish: review ${strugglingBlockers.join(", ")} to solidify your foundation before moving forward.)`;
    }
    if (deficitLessons.length > 0) {
      note += ` [Note: ${deficitLessons.slice(0, 3).join(", ")} have card deficits (< 5 cards). Type '/cards for [lesson]' anytime to generate more.]`;
    }
    desc.textContent = note;
  } else {
    banner.className = "progression-banner gated";
    icon.textContent = "⚠️";
    title.textContent = `Advisory: Review Recommended Before Starting ${nextLesson.code}`;
    desc.textContent = `Active struggling lessons (${strugglingCountSoFar}/${MAX_STRUGGLING_ALLOWED} allowed) require a quick review before advancing: ${strugglingBlockers.join(", ")}. We recommend reviewing these cards before formalizing ${nextLesson.code} in Notion, though you are free to proceed at your own pace.`;
  }
}

function getGeneralAndSneakPeekCards(unlockedCodes) {
  return state.cards.filter(c => {
    const primary = c.primary_lesson || (c.lesson_codes && c.lesson_codes[0]);
    if (!primary || primary === "general" || c.is_general) {
      return true;
    }
    return !unlockedCodes.has(primary);
  });
}

function renderGeneralSection(curriculumState) {
  const { unlockedCodes } = curriculumState;
  const generalCards = getGeneralAndSneakPeekCards(unlockedCodes);

  // Tally sneak-peeks
  const sneakPeeks = {};
  let pureGeneralCount = 0;
  generalCards.forEach(c => {
    const primary = c.primary_lesson || (c.lesson_codes && c.lesson_codes[0]);
    if (primary && primary !== "general" && !unlockedCodes.has(primary)) {
      sneakPeeks[primary] = (sneakPeeks[primary] || 0) + 1;
    } else {
      pureGeneralCount++;
    }
  });

  document.getElementById("general-card-count").textContent = `${generalCards.length} cards`;
  const badgeContainer = document.getElementById("peek-badges-container");
  badgeContainer.innerHTML = "";

  Object.keys(sneakPeeks).sort().forEach(code => {
    const badge = document.createElement("span");
    badge.className = "peek-badge";
    badge.textContent = `Sneak Peek: ${code} (${sneakPeeks[code]})`;
    badgeContainer.appendChild(badge);
  });

  if (pureGeneralCount > 0) {
    const pBadge = document.createElement("span");
    pBadge.className = "peek-badge";
    pBadge.style.color = "#94a3b8";
    pBadge.style.borderColor = "#334155";
    pBadge.textContent = `Conversational / Slang (${pureGeneralCount})`;
    badgeContainer.appendChild(pBadge);
  }
}

function renderCurriculumList(curriculumState) {
  const { lessonMap } = curriculumState;
  const container = document.getElementById("curriculum-container");
  container.innerHTML = "";

  const levels = [
    { key: "A0", title: "🟢 Level A0: Absolute Beginner (Foundations)" },
    { key: "A1", title: "🟡 Level A1: Elementary Spoken Hindi" },
    { key: "A2", title: "🔴 Level A2: Pre-Intermediate Spoken Hindi" }
  ];

  levels.forEach(lvl => {
    const lessonsInLevel = state.curriculum.filter(l => l.level === lvl.key);
    if (lessonsInLevel.length === 0) return;

    const groupDiv = document.createElement("div");
    groupDiv.className = "level-group";

    const headerDiv = document.createElement("div");
    headerDiv.className = "level-header";
    headerDiv.innerHTML = `
      <h3 class="level-title">${lvl.title}</h3>
      <span class="level-meta">${lessonsInLevel.length} Lessons</span>
    `;
    groupDiv.appendChild(headerDiv);

    const tableHeader = document.createElement("div");
    tableHeader.className = "lesson-list-header";
    tableHeader.innerHTML = `
      <span class="col-header col-code">Code</span>
      <span class="col-header col-info">Lesson & Topics</span>
      <span class="col-header col-bar">Progress</span>
      <span class="col-header col-cards">Deck Cards</span>
      <span class="col-header col-status">Status</span>
    `;
    groupDiv.appendChild(tableHeader);

    const listDiv = document.createElement("div");
    listDiv.className = "lesson-list";

    lessonsInLevel.forEach(l => {
      const data = lessonMap[l.code];
      const isLocked = data.status === "Locked";
      const total = data.cards.length;

      const row = document.createElement("div");
      row.className = `lesson-row ${isLocked ? "locked" : ""}`;

      // Mini bar segments
      let barHtml = "";
      if (total > 0 && !isLocked) {
        const mP = (data.masteredCount / total) * 100;
        const lP = (data.learningCount / total) * 100;
        const sP = (data.strugglingCount / total) * 100;
        barHtml = `
          <div class="mini-bar">
            <div class="mini-segment mastered" style="width: ${mP}%"></div>
            <div class="mini-segment learning" style="width: ${lP}%"></div>
            <div class="mini-segment struggling" style="width: ${sP}%"></div>
          </div>
        `;
      }

      // Status pill text
      let pillClass = data.status.toLowerCase().replace(/\s+/g, "-");
      let pillText = data.status;
      let cardCountText = `${total} cards`;

      if (data.code === "A0-X") {
        pillClass = "reference";
        pillText = "📘 Reference";
        cardCountText = "Universal (182)";
        barHtml = `<div class="mini-bar"><div class="mini-segment mastered" style="width: 100%; background: #38bdf8;"></div></div>`;
      } else if (data.status === "Locked") {
        pillText = "🔒 Locked";
        cardCountText = total > 0 ? `${total} preview cards` : "0 cards";
      } else if (data.status === "Needs Cards") {
        pillClass = "needs-cards";
        pillText = `⚪ Needs Cards (${total}/${MIN_CARDS_PER_LESSON})`;
      } else if (data.status === "Mastered") {
        pillText = "🟢 Mastered";
      } else if (data.status === "Learning") {
        pillText = "🟡 Learning";
      } else if (data.status === "Struggling") {
        pillText = "🔴 Struggling";
      }

      if (!barHtml) {
        barHtml = `<div class="mini-bar empty" title="No active study cards in deck yet"></div>`;
      }

      const summarySnippet = data.summary.slice(0, 2).join(" • ");

      row.innerHTML = `
        <div class="lesson-col col-code">
          <span class="lesson-code-box">${data.code}</span>
        </div>
        <div class="lesson-col col-info">
          <div class="lesson-title">${data.title}</div>
          <div class="lesson-summary-preview">${summarySnippet || "Foundational concepts"}</div>
        </div>
        <div class="lesson-col col-bar">
          ${barHtml}
        </div>
        <div class="lesson-col col-cards">
          <span class="card-count-badge ${data.code === "A0-X" ? "ref-badge" : ""}">${cardCountText}</span>
        </div>
        <div class="lesson-col col-status">
          <span class="status-pill ${pillClass}">${pillText}</span>
        </div>
      `;

      if (!isLocked) {
        row.addEventListener("click", () => {
          navigateTo(`#lesson/${data.code}`);
        });
      } else {
        row.title = "Lesson not yet created in Notion. Create Notion page to unlock.";
      }

      listDiv.appendChild(row);
    });

    groupDiv.appendChild(listDiv);
    container.appendChild(groupDiv);
  });
}

// --- LESSON DETAIL VIEW ---
function renderLessonDetail(code, curriculumState) {
  const { lessonMap } = curriculumState;
  const lesson = lessonMap[code];
  if (!lesson) {
    navigateTo("#overview");
    return;
  }

  document.getElementById("detail-code").textContent = lesson.code;
  document.getElementById("detail-title").textContent = lesson.title;
  document.getElementById("detail-level").textContent = lesson.level_name;

  let pillClass = lesson.status.toLowerCase();
  let pillText = lesson.status;
  if (lesson.status === "Incomplete") pillText = `Incomplete (${lesson.cards.length}/${MIN_CARDS_PER_LESSON})`;
  else if (lesson.status === "Mastered") pillText = "🟢 Mastered";
  else if (lesson.status === "Learning") pillText = "🟡 Learning";
  else if (lesson.status === "Struggling") pillText = "🔴 Struggling";

  const pill = document.getElementById("detail-status-pill");
  pill.className = `status-pill ${pillClass}`;
  pill.textContent = pillText;

  // Notion button
  const notionBtn = document.getElementById("detail-notion-btn");
  notionBtn.href = lesson.notion_url || "#";

  // Summary box
  const summaryList = document.getElementById("detail-summary-list");
  summaryList.innerHTML = "";
  lesson.summary.forEach(point => {
    const li = document.createElement("li");
    li.textContent = point;
    summaryList.appendChild(li);
  });

  // Diya action button
  const diyaBtn = document.getElementById("detail-diya-btn");
  diyaBtn.onclick = () => {
    const prompt = `/cards for ${lesson.code}`;
    navigator.clipboard.writeText(prompt);
    showToast(`Copied prompt: "${prompt}" to clipboard!`);
  };

  renderCardGrid(lesson.cards);
}

// --- GENERAL VIEW ---
function renderGeneralView(curriculumState) {
  const { unlockedCodes } = curriculumState;
  const generalCards = getGeneralAndSneakPeekCards(unlockedCodes);

  document.getElementById("general-total-count").textContent = `${generalCards.length} cards`;
  renderCardGrid(generalCards, true);
}

function renderCardGrid(cards, isGeneralView = false) {
  const container = document.getElementById(isGeneralView ? "general-card-grid" : "detail-card-grid");
  container.innerHTML = "";

  // Filter cards
  let filtered = cards;
  if (state.cardFilter !== "all") {
    filtered = filtered.filter(c => c.status.toLowerCase() === state.cardFilter.toLowerCase());
  }

  if (state.searchQuery.trim()) {
    const q = state.searchQuery.toLowerCase();
    filtered = filtered.filter(c => 
      c.front.toLowerCase().includes(q) || 
      c.back.toLowerCase().includes(q)
    );
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; padding: 40px 20px; text-align: center; color: #94a3b8; background: var(--bg-card); border-radius: 12px; border: 1px dashed var(--border-subtle);">
        <p style="font-size: 1.1rem; margin-bottom: 8px;">No cards found matching current filters.</p>
        <p style="font-size: 0.85rem; color: #64748b;">Try adjusting your search query or status filter.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(c => {
    const cardEl = document.createElement("div");
    cardEl.className = `anki-card status-${c.status.toLowerCase()}`;

    let statusPill = "";
    if (c.status === "Mastered") statusPill = `<span class="status-pill mastered">🟢 Mastered (${c.interval}d)</span>`;
    else if (c.status === "Learning") statusPill = `<span class="status-pill learning">🟡 Learning (${c.interval}d)</span>`;
    else statusPill = `<span class="status-pill struggling">🔴 Struggling (${c.interval}d, ${c.lapses} lapses)</span>`;

    // Lesson tag or sneak-peek badge
    let lessonTagHtml = "";
    if (c.lesson_codes && c.lesson_codes.length > 0) {
      lessonTagHtml = c.lesson_codes.map(code => `<span class="peek-badge" style="font-size: 0.72rem; padding: 2px 8px;">${code}</span>`).join(" ");
    }

    let focusHtml = "";
    if (c.target_focus) {
      focusHtml = `<div class="target-focus-pill">🎯 Focus: ${c.target_focus}</div>`;
    }

    cardEl.innerHTML = `
      <div class="card-top">
        ${statusPill}
        <div class="card-stats">
          <span>Reps: ${c.reps}</span>
          <span>•</span>
          <span>Lapses: ${c.lapses}</span>
          <span>•</span>
          <span>Ease: ${Math.round(c.factor / 10)}%</span>
        </div>
      </div>
      ${focusHtml}
      <div class="card-front">${c.front}</div>
      <div class="card-back">${c.back}</div>
      <div class="card-footer">
        <div>${lessonTagHtml}</div>
        <span>Note #${c.noteId}</span>
      </div>
    `;
    container.appendChild(cardEl);
  });
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

// --- ROUTER ---
function navigateTo(hash) {
  window.location.hash = hash;
}

function handleRoute() {
  const hash = window.location.hash || "#overview";
  state.cardFilter = "all";
  state.searchQuery = "";

  // Reset tab buttons
  document.querySelectorAll(".filter-tab").forEach(t => {
    t.classList.toggle("active", t.dataset.filter === "all");
  });
  document.querySelectorAll(".search-input").forEach(i => i.value = "");

  const curriculumState = computeCurriculumState();

  if (hash === "#overview" || hash === "") {
    state.activeView = "overview";
    document.getElementById("view-overview").className = "view-container active";
    document.getElementById("view-lesson-detail").className = "view-container";
    document.getElementById("view-general").className = "view-container";

    renderProgressionBanner(curriculumState);
    renderGeneralSection(curriculumState);
    renderCurriculumList(curriculumState);
  } else if (hash === "#general") {
    state.activeView = "general";
    document.getElementById("view-overview").className = "view-container";
    document.getElementById("view-lesson-detail").className = "view-container";
    document.getElementById("view-general").className = "view-container active";

    renderGeneralView(curriculumState);
  } else if (hash.startsWith("#lesson/")) {
    const code = hash.replace("#lesson/", "");
    if (!curriculumState.unlockedCodes.has(code)) {
      showToast(`Lesson ${code} is locked! Notion page has not been created yet.`);
      navigateTo("#overview");
      return;
    }
    state.activeView = "lesson";
    state.activeLessonCode = code;
    document.getElementById("view-overview").className = "view-container";
    document.getElementById("view-lesson-detail").className = "view-container active";
    document.getElementById("view-general").className = "view-container";

    renderLessonDetail(code, curriculumState);
  }
}

// --- INITIALIZATION ---
async function init() {
  try {
    state.curriculum = await loadCurriculumData();
    const deckData = await loadDeckData();
    state.cards = deckData.cards || [];
    state.isLive = deckData.is_live || false;
    state.syncedAt = deckData.synced_at;

    renderHeader();
    const curriculumState = computeCurriculumState();
    renderStats(curriculumState);

    // Event listeners
    window.addEventListener("hashchange", handleRoute);

    // Refresh sync button
    document.getElementById("refresh-btn").addEventListener("click", async () => {
      showToast("Syncing with AnkiConnect...");
      try {
        const fresh = await loadDeckData();
        state.cards = fresh.cards || [];
        state.isLive = fresh.is_live || false;
        state.syncedAt = fresh.synced_at;
        renderHeader();
        const updatedState = computeCurriculumState();
        renderStats(updatedState);
        handleRoute();
        showToast(state.isLive ? "Live Anki data updated!" : "Snapshot reloaded.");
      } catch (err) {
        showToast("Sync error: " + err.message);
      }
    });

    // General card section click
    document.getElementById("general-card-section").addEventListener("click", () => {
      navigateTo("#general");
    });

    // Filter tabs
    document.querySelectorAll(".filter-tab").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const filter = e.target.dataset.filter;
        state.cardFilter = filter;
        document.querySelectorAll(".filter-tab").forEach(b => b.classList.remove("active"));
        e.target.classList.add("active");

        const curState = computeCurriculumState();
        if (state.activeView === "lesson") {
          const l = curState.lessonMap[state.activeLessonCode];
          renderCardGrid(l ? l.cards : []);
        } else if (state.activeView === "general") {
          renderGeneralView(curState);
        }
      });
    });

    // Search inputs
    document.querySelectorAll(".search-input").forEach(inp => {
      inp.addEventListener("input", (e) => {
        state.searchQuery = e.target.value;
        const curState = computeCurriculumState();
        if (state.activeView === "lesson") {
          const l = curState.lessonMap[state.activeLessonCode];
          renderCardGrid(l ? l.cards : []);
        } else if (state.activeView === "general") {
          renderGeneralView(curState);
        }
      });
    });

    // Initial route
    handleRoute();

  } catch (err) {
    console.error("Initialization error:", err);
    document.body.innerHTML = `
      <div style="padding: 40px; text-align: center; color: #ef4444;">
        <h2>Failed to load Lessons Dashboard</h2>
        <p style="margin-top: 10px; color: #94a3b8;">${err.message}</p>
      </div>
    `;
  }
}

document.addEventListener("DOMContentLoaded", init);
