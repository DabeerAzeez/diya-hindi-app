/**
 * Hindi Lessons & Anki Coverage Dashboard
 * Classic standalone JavaScript bundle (No ES module imports, zero CORS friction).
 */

(function () {
  "use strict";

  const MIN_CARDS_PER_LESSON = 5;
  const MAX_STRUGGLING_ALLOWED = 2;
  const MAX_LEARNING_ALLOWED = 6;

  const state = {
    curriculum: [],
    cards: [],
    lexicon: window.HIGH_ROI_LEXICON || null,
    isLive: false,
    isServerLive: false,
    syncedAt: null,
    activeView: "overview", // "overview" | "lesson" | "general" | "lexicon"
    activeLessonCode: null,
    cardFilter: "all",
    searchQuery: "",
    lexiconCategory: "all",
    lexiconCoverageFilter: "all",
    lexiconSearchQuery: ""
  };

  // --- PROGRESSION & GATING ENGINE ---
  function computeCurriculumState() {
    const lessonMap = {};
    state.curriculum.forEach(function (l) {
      lessonMap[l.code] = {
        code: l.code,
        title: l.title,
        level: l.level,
        level_name: l.level_name,
        summary: l.summary || [],
        notion_url: l.notion_url || "#",
        is_completed: !!l.is_completed,
        is_active: !!l.is_active,
        cards: [],
        status: "Locked",
        masteredCount: 0,
        learningCount: 0,
        strugglingCount: 0
      };
    });

    // Populate cards into lessons using primary ceiling lesson
    state.cards.forEach(function (card) {
      const primaryCode = card.primary_lesson || (card.lesson_codes && card.lesson_codes[0]);
      if (!primaryCode || primaryCode === "general" || card.is_general) {
        return; // pure general or sneak peek
      }
      if (lessonMap[primaryCode]) {
        lessonMap[primaryCode].cards.push(card);
      }
    });

    const unlockedCodes = new Set();
    let strugglingCountSoFar = 0;
    let learningCountSoFar = 0;
    let incompleteCountSoFar = 0;

    for (let i = 0; i < state.curriculum.length; i++) {
      const lesson = state.curriculum[i];
      const code = lesson.code;
      const lData = lessonMap[code];
      const totalCards = lData.cards.length;

      let m = 0, l = 0, s = 0;
      lData.cards.forEach(function (c) {
        if (c.status === "Mastered") m++;
        else if (c.status === "Learning") l++;
        else if (c.status === "Struggling") s++;
      });
      lData.masteredCount = m;
      lData.learningCount = l;
      lData.strugglingCount = s;

      // Special handling for A0-X: Phonetics & Pronunciation Baseline
      if (code === "A0-X") {
        unlockedCodes.add(code);
        lData.status = "Reference";
        continue; // Universal reference baseline, zero debt
      }

      // STRICT NOTION CAP & ACTIVE LESSON UNLOCK:
      // A lesson is unlocked if completed in Notion OR if it is the current active lesson currently being studied!
      const isCompletedInNotion = !!lesson.is_completed;
      const isCurrentActive = !!lesson.is_active;
      const isUnlocked = isCompletedInNotion || isCurrentActive;

      if (isUnlocked) {
        unlockedCodes.add(code);

        const sRate = totalCards > 0 ? (s / totalCards) : 0;
        const mRate = totalCards > 0 ? (m / totalCards) : 0;

        if (isCurrentActive && !isCompletedInNotion) {
          if (totalCards < MIN_CARDS_PER_LESSON) {
            lData.status = "Needs Cards";
            incompleteCountSoFar++;
          } else {
            lData.status = "Active";
            learningCountSoFar++;
          }
        } else if (totalCards < MIN_CARDS_PER_LESSON) {
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
      lessonMap: lessonMap,
      unlockedCodes: unlockedCodes,
      strugglingCountSoFar: strugglingCountSoFar,
      learningCountSoFar: learningCountSoFar,
      incompleteCountSoFar: incompleteCountSoFar
    };
  }


  // --- RENDER FUNCTIONS ---
  function renderHeader() {
    const syncDot = document.getElementById("sync-dot");
    const syncLabel = document.getElementById("sync-label");
    if (state.isLive) {
      syncDot.className = "sync-dot live";
      syncLabel.textContent = "Live Anki Desktop";
    } else {
      syncDot.className = "sync-dot";
      const dateStr = state.syncedAt ? new Date(state.syncedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Local";
      syncLabel.textContent = "Snapshot Synced (" + dateStr + ")";
    }
  }

  function renderStats() {
    const totalCards = state.cards.length;
    let mastered = 0, learning = 0, struggling = 0;
    state.cards.forEach(function (c) {
      if (c.status === "Mastered") mastered++;
      else if (c.status === "Learning") learning++;
      else if (c.status === "Struggling") struggling++;
    });

    const mPct = totalCards > 0 ? Math.round((mastered / totalCards) * 100) : 0;
    const lPct = totalCards > 0 ? Math.round((learning / totalCards) * 100) : 0;
    const sPct = totalCards > 0 ? Math.round((struggling / totalCards) * 100) : 0;

    document.getElementById("stat-total-cards").textContent = totalCards;
    document.getElementById("stat-mastered").textContent = mastered + " (" + mPct + "%)";
    document.getElementById("stat-learning").textContent = learning + " (" + lPct + "%)";
    document.getElementById("stat-struggling").textContent = struggling + " (" + sPct + "%)";
  }

  function getGeneralAndSneakPeekCards(unlockedCodes) {
    return state.cards.filter(function (c) {
      const primary = c.primary_lesson || (c.lesson_codes && c.lesson_codes[0]);
      if (!primary || primary === "general" || c.is_general) {
        return true;
      }
      return !unlockedCodes.has(primary);
    });
  }

  function renderProgressionBanner(curriculumState) {
    const banner = document.getElementById("progression-banner");
    const icon = document.getElementById("banner-icon");
    const title = document.getElementById("banner-title");
    const desc = document.getElementById("banner-desc");

    const lessonMap = curriculumState.lessonMap;
    const strugglingCountSoFar = curriculumState.strugglingCountSoFar;
    const learningCountSoFar = curriculumState.learningCountSoFar;
    const incompleteCountSoFar = curriculumState.incompleteCountSoFar;

    let activeLesson = null;
    let nextLesson = null;
    for (let i = 0; i < state.curriculum.length; i++) {
      const l = state.curriculum[i];
      if (l.is_active) {
        activeLesson = l;
      }
      if (!nextLesson && lessonMap[l.code].status === "Locked") {
        nextLesson = l;
      }
    }

    const strugglingBlockers = [];
    const deficitLessons = [];
    state.curriculum.forEach(function (l) {
      const s = lessonMap[l.code].status;
      if (s === "Struggling") {
        strugglingBlockers.push(l.code + " (" + lessonMap[l.code].strugglingCount + " failing cards)");
      } else if (s === "Needs Cards" && l.is_completed) {
        deficitLessons.push(l.code + " (" + lessonMap[l.code].cards.length + "/" + MIN_CARDS_PER_LESSON + ")");
      }
    });

    if (activeLesson) {
      banner.className = "progression-banner ready";
      icon.textContent = "⚡";
      title.textContent = "Active Lesson In Progress: " + activeLesson.code + ": " + activeLesson.title;
      const curCardCount = lessonMap[activeLesson.code] ? lessonMap[activeLesson.code].cards.length : 0;
      let note = "Lesson " + activeLesson.code + " is currently open for study (" + curCardCount + " deck cards). Upcoming milestone: " + (nextLesson ? nextLesson.code + " (" + nextLesson.title + ")" : "Level Capstone") + ".";
      if (strugglingBlockers.length > 0) {
        note += " (Recommended review: " + strugglingBlockers.join(", ") + " to keep prerequisite retention high.)";
      }
      desc.textContent = note;
      return;
    }

    if (!nextLesson) {
      banner.className = "progression-banner ready";
      icon.textContent = "🎉";
      title.textContent = "All Curriculum Modules Completed in Notion!";
      desc.textContent = "You have completed all lessons across A0, A1, and A2 in Notion. Keep practicing in Anki to maintain Mastered status!";
      return;
    }

    if (strugglingCountSoFar <= MAX_STRUGGLING_ALLOWED) {
      banner.className = "progression-banner ready";
      icon.textContent = "🚀";
      title.textContent = "Advisory: Ready to Advance to " + nextLesson.code + ": " + nextLesson.title;
      let note = "Active prerequisite debt is within healthy targets (" + strugglingCountSoFar + "/" + MAX_STRUGGLING_ALLOWED + " Struggling allowed). You are conceptually ready to create and study Lesson " + nextLesson.code + " in Notion whenever you choose!";
      if (strugglingBlockers.length > 0) {
        note += " (Recommended polish: review " + strugglingBlockers.join(", ") + " to solidify your foundation before moving forward.)";
      }
      if (deficitLessons.length > 0) {
        note += " [Note: " + deficitLessons.slice(0, 3).join(", ") + " have card deficits (< 5 cards). Type '/cards for [lesson]' anytime to generate more.]";
      }
      desc.textContent = note;
    } else {
      banner.className = "progression-banner gated";
      icon.textContent = "⚠️";
      title.textContent = "Advisory: Review Recommended Before Starting " + nextLesson.code;
      desc.textContent = "Active struggling lessons (" + strugglingCountSoFar + "/" + MAX_STRUGGLING_ALLOWED + " allowed) require a quick review before advancing: " + strugglingBlockers.join(", ") + ". We recommend reviewing these cards before formalizing " + nextLesson.code + " in Notion, though you are free to proceed at your own pace.";
    }
  }

  function renderGeneralSection(curriculumState) {
    const unlockedCodes = curriculumState.unlockedCodes;
    const generalCards = getGeneralAndSneakPeekCards(unlockedCodes);

    const sneakPeeks = {};
    let pureGeneralCount = 0;
    generalCards.forEach(function (c) {
      const primary = c.primary_lesson || (c.lesson_codes && c.lesson_codes[0]);
      if (primary && primary !== "general" && !unlockedCodes.has(primary)) {
        sneakPeeks[primary] = (sneakPeeks[primary] || 0) + 1;
      } else {
        pureGeneralCount++;
      }
    });

    document.getElementById("general-card-count").textContent = generalCards.length + " cards";
    const badgeContainer = document.getElementById("peek-badges-container");
    badgeContainer.innerHTML = "";

    Object.keys(sneakPeeks).sort().forEach(function (code) {
      const badge = document.createElement("span");
      badge.className = "peek-badge";
      badge.textContent = "Sneak Peek: " + code + " (" + sneakPeeks[code] + ")";
      badgeContainer.appendChild(badge);
    });

    if (pureGeneralCount > 0) {
      const pBadge = document.createElement("span");
      pBadge.className = "peek-badge";
      pBadge.style.color = "#94a3b8";
      pBadge.style.borderColor = "#334155";
      pBadge.textContent = "Conversational / Slang (" + pureGeneralCount + ")";
      badgeContainer.appendChild(pBadge);
    }
  }

  function renderCurriculumList(curriculumState) {
    const lessonMap = curriculumState.lessonMap;
    const container = document.getElementById("curriculum-container");
    container.innerHTML = "";

    const levels = [
      { key: "A0", title: "🟢 Level A0: Absolute Beginner (Foundations)" },
      { key: "A1", title: "🟡 Level A1: Elementary Spoken Hindi" },
      { key: "A2", title: "🔴 Level A2: Pre-Intermediate Spoken Hindi" }
    ];

    levels.forEach(function (lvl) {
      const lessonsInLevel = state.curriculum.filter(function (l) { return l.level === lvl.key; });
      if (lessonsInLevel.length === 0) return;

      const groupDiv = document.createElement("div");
      groupDiv.className = "level-group";

      const headerDiv = document.createElement("div");
      headerDiv.className = "level-header";
      headerDiv.innerHTML = '<h3 class="level-title">' + lvl.title + '</h3><span class="level-meta">' + lessonsInLevel.length + ' Lessons</span>';
      groupDiv.appendChild(headerDiv);

      const tableHeader = document.createElement("div");
      tableHeader.className = "lesson-list-header";
      tableHeader.innerHTML =
        '<span class="col-header col-code">Code</span>' +
        '<span class="col-header col-info">Lesson & Topics</span>' +
        '<span class="col-header col-bar">Progress</span>' +
        '<span class="col-header col-cards">Deck Cards</span>' +
        '<span class="col-header col-status">Status</span>';
      groupDiv.appendChild(tableHeader);

      const listDiv = document.createElement("div");
      listDiv.className = "lesson-list";

      lessonsInLevel.forEach(function (l) {
        const data = lessonMap[l.code];
        const isLocked = data.status === "Locked";
        const total = data.cards.length;

        const row = document.createElement("div");
        row.className = "lesson-row " + (isLocked ? "locked" : "");

        let barHtml = "";
        if (total > 0 && !isLocked) {
          const mP = (data.masteredCount / total) * 100;
          const lP = (data.learningCount / total) * 100;
          const sP = (data.strugglingCount / total) * 100;
          barHtml = '<div class="mini-bar">' +
            '<div class="mini-segment mastered" style="width: ' + mP + '%"></div>' +
            '<div class="mini-segment learning" style="width: ' + lP + '%"></div>' +
            '<div class="mini-segment struggling" style="width: ' + sP + '%"></div>' +
          '</div>';
        }

        let pillClass = data.status.toLowerCase().replace(/\s+/g, "-");
        let pillText = data.status;
        let cardCountText = total + " cards";

        if (data.code === "A0-X") {
          pillClass = "reference";
          pillText = "📘 Reference";
          cardCountText = "Universal (182)";
          barHtml = '<div class="mini-bar"><div class="mini-segment mastered" style="width: 100%; background: #38bdf8;"></div></div>';
        } else if (data.status === "Active") {
          pillClass = "learning";
          pillText = "⚡ Active (" + total + " cards)";
        } else if (data.status === "Needs Cards") {
          pillClass = "needs-cards";
          pillText = "⚪ Needs Cards (" + total + "/" + MIN_CARDS_PER_LESSON + ")";
        } else if (data.status === "Locked") {
          pillText = "🔒 Locked";
          cardCountText = total > 0 ? (total + " preview cards") : "0 cards";
        } else if (data.status === "Mastered") {
          pillText = "🟢 Mastered";
        } else if (data.status === "Learning") {
          pillText = "🟡 Learning";
        } else if (data.status === "Struggling") {
          pillText = "🔴 Struggling";
        }

        if (!barHtml) {
          barHtml = '<div class="mini-bar empty" title="No active study cards in deck yet"></div>';
        }

        const summarySnippet = data.summary.slice(0, 2).join(" • ");

        row.innerHTML =
          '<div class="lesson-col col-code">' +
            '<span class="lesson-code-box">' + data.code + '</span>' +
          '</div>' +
          '<div class="lesson-col col-info">' +
            '<div class="lesson-title">' + data.title + '</div>' +
            '<div class="lesson-summary-preview">' + (summarySnippet || "Core grammar concepts") + '</div>' +
          '</div>' +
          '<div class="lesson-col col-bar">' +
            barHtml +
          '</div>' +
          '<div class="lesson-col col-cards">' +
            '<span class="card-count-badge' + (data.code === "A0-X" ? " ref-badge" : "") + '">' + cardCountText + '</span>' +
          '</div>' +
          '<div class="lesson-col col-status">' +
            '<span class="status-pill ' + pillClass + '">' + pillText + '</span>' +
          '</div>';

        if (!isLocked) {
          row.addEventListener("click", function () {
            navigateTo("#lesson/" + data.code);
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
    const lessonMap = curriculumState.lessonMap;
    const lesson = lessonMap[code];
    if (!lesson) {
      navigateTo("#overview");
      return;
    }

    document.getElementById("detail-code").textContent = lesson.code;
    document.getElementById("detail-title").textContent = lesson.title;
    document.getElementById("detail-level").textContent = lesson.level_name;

    let pillClass = lesson.status.toLowerCase().replace(/\s+/g, "-");
    let pillText = lesson.status;
    if (lesson.code === "A0-X") {
      pillClass = "reference";
      pillText = "📘 Reference Foundation";
    } else if (lesson.status === "Active") {
      pillClass = "learning";
      pillText = "⚡ Active (" + lesson.cards.length + " cards)";
    } else if (lesson.status === "Needs Cards") {
      pillClass = "needs-cards";
      pillText = "⚪ Needs Cards (" + lesson.cards.length + "/" + MIN_CARDS_PER_LESSON + ")";
    } else if (lesson.status === "Mastered") {
      pillText = "🟢 Mastered";
    } else if (lesson.status === "Learning") {
      pillText = "🟡 Learning";
    } else if (lesson.status === "Struggling") {
      pillText = "🔴 Struggling";
    }

    const pill = document.getElementById("detail-status-pill");
    pill.className = "status-pill " + pillClass;
    pill.textContent = pillText;

    const notionBtn = document.getElementById("detail-notion-btn");
    notionBtn.href = lesson.notion_url || "#";

    const summaryList = document.getElementById("detail-summary-list");
    summaryList.innerHTML = "";
    lesson.summary.forEach(function (point) {
      const li = document.createElement("li");
      li.textContent = point;
      summaryList.appendChild(li);
    });

    const genCardsBtn = document.getElementById("detail-generate-cards-btn");
    if (genCardsBtn) {
      if (lesson.code === "A0-X" || lesson.status === "Locked") {
        genCardsBtn.style.display = "none";
      } else {
        genCardsBtn.style.display = "inline-flex";
        if (lesson.status === "Needs Cards") {
          genCardsBtn.className = "btn btn-secondary btn-generate-highlight";
          genCardsBtn.innerHTML = "<span>✨ Generate Cards (Needs Cards)</span>";
        } else {
          genCardsBtn.className = "btn btn-secondary";
          genCardsBtn.innerHTML = "<span>✨ Generate Cards</span>";
        }
        genCardsBtn.onclick = function () {
          openCardGenerationModal(lesson.code, lesson.title, curriculumState);
        };
      }
    }

    renderCardGrid(lesson.cards, false, lesson.code === "A0-X");
  }

  // --- GENERAL VIEW ---
  function renderGeneralView(curriculumState) {
    const unlockedCodes = curriculumState.unlockedCodes;
    const generalCards = getGeneralAndSneakPeekCards(unlockedCodes);

    document.getElementById("general-total-count").textContent = generalCards.length + " cards";
    renderCardGrid(generalCards, true);
  }

  // --- HIGH-ROI LEXICON COVERAGE ENGINE ---
  const VERB_STEM_OVERRIDES = {
    'karnaa': [/\bkar/i, /\bkiy[aie]+/i, /\bkijiy/i],
    'honaa': [/\bho/i, /\bhuaa?\b/i, /\bhui\b/i, /\bhue\b/i, /\bhotaa?\b/i, /\bhoti\b/i, /\bhote\b/i],
    'jaanaa': [/\bjaa/i, /\bgay[aie]+\b/i],
    'aanaa': [/\baa[ntoyeg]/i, /\baay[aie]+\b/i, /\baao\b/i, /\baaiy/i],
    'lenaa': [/\ble[ntoged]/i, /\bliy[aie]+\b/i, /\blijiye\b/i, /\blee\b/i],
    'denaa': [/\bde[ntoged]/i, /\bdiy[aie]+\b/i, /\bdijiye\b/i, /\bdee\b/i],
    'bolnaa': [/\bbol/i],
    'kehnaa': [/\bkeh/i, /\bkah[aie]+/i],
    'bataanaa': [/\bbataa/i],
    'baat karnaa': [/\bbaat\s+kar/i, /\bbaat\s+kiy/i, /\bbaat\s+karn/i],
    'dekhnaa': [/\bdekh/i],
    'sunnaa': [/\bsun/i],
    'samajhnaa': [/\bsamajh/i],
    'sochnaa': [/\bsoch/i],
    'jaannaa': [/\bjaan/i],
    'pataa honaa': [/\bpataa?\b/i],
    'rakhnaa': [/\brakh/i],
    'chhodnaa': [/\bchhod/i, /\bchod/i],
    'uthaanaa': [/\buthaa/i],
    'pakadnaa': [/\bpakad/i],
    'pahunchnaa': [/\bpahunch/i],
    'nikalnaa': [/\bnikal/i],
    'ruknaa': [/\bruk/i],
    'roknaa': [/\brok/i],
    'chalnaa': [/\bchal[ntogeaiy]/i],
    'chalaanaa': [/\bchalaa/i],
    'baithnaa': [/\bbaith/i],
    'khadaa honaa': [/\bkhad[aie]+\s+ho/i],
    'milnaa': [/\bmil/i],
    'dhoondhnaa': [/\bdhoondh/i, /\bdhundh/i],
    'bhejnaa': [/\bbhej/i],
    'laanaa': [/\blaa[ntoyeg]/i, /\blaay[aie]+\b/i],
    'le jaanaa': [/\ble\s+jaa/i, /\ble\s+gay/i],
    'khaanaa': [/\bkhaa[ntoyeg]/i, /\bkhaay[aie]+\b/i],
    'peenaa': [/\bpee[ntoyeg]/i, /\bpeey[aie]+\b/i, /\bpiy[aie]+\b/i],
    'sonaa': [/\bso[ntoyeg]/i, /\bsoy[aie]+\b/i],
    'uthnaa': [/\buth[ntogeaiy]/i],
    'hansnaa': [/\bhans/i, /\bhas/i],
    'ronaa': [/\bro[ntoyeg]/i, /\broy[aie]+\b/i],
    'bhoolnaa': [/\bbhool/i, /\bbhul/i],
    'yaad aanaa': [/\byaad\b/i],
    'maangnaa': [/\bmaang/i],
    'khelnaa': [/\bkhel/i],
    'bajaanaa': [/\bbajaa/i],
    'seekhnaa': [/\bseekh/i, /\bsikh[ntog]/i],
    'sikhaanaa': [/\bsikhaa/i],
    'sambhaalnaa': [/\bsambhaal/i],
    'bachnaa': [/\bbach/i],
    'girnaa': [/\bgir/i],
    'lagnaa': [/\blag/i]
  };

  function normalizeHindiText(text) {
    if (!text) return "";
    var t = text.replace(/<[^>]+>/g, " ").toLowerCase();
    t = t.replace(/[āàâä]/g, "aa");
    t = t.replace(/[īíîï]/g, "ee");
    t = t.replace(/[ūúûü]/g, "oo");
    t = t.replace(/[ṛř]/g, "r");
    t = t.replace(/[ḍ]/g, "d");
    t = t.replace(/[ṭ]/g, "t");
    t = t.replace(/[ṅñṇṁṃ]/g, "n");
    t = t.replace(/['".,?!/\\:;()\-]/g, " ");
    return t.replace(/\s+/g, " ").trim();
  }

  function getWordPatterns(word, category) {
    var raw = word.toLowerCase().trim();
    if (category === "verbs" && VERB_STEM_OVERRIDES[raw]) {
      return VERB_STEM_OVERRIDES[raw];
    }
    var subWords = raw.split("/").map(function (s) { return s.trim(); });
    var patterns = [];
    subWords.forEach(function (sw) {
      if (sw.indexOf(" ") !== -1) {
        var parts = sw.split(/\s+/);
        var stem0 = parts[0].replace(/[aeiou]+$/, "");
        var stem1 = parts[1].replace(/[aeiou]+$/, "");
        patterns.push(new RegExp("\\b" + stem0 + "\\w*\\s+" + stem1 + "\\w*", "i"));
      } else {
        var stem = sw.replace(/[aeiou]+$/, "");
        if (stem.length >= 3) {
          patterns.push(new RegExp("\\b" + stem + "[aieou]*\\b", "i"));
        } else {
          patterns.push(new RegExp("\\b" + sw + "\\b", "i"));
        }
      }
    });
    return patterns;
  }

  function computeLexiconCoverage() {
    if (!state.lexicon) return null;
    var cards = state.cards;
    var normCards = cards.map(function (c) {
      return {
        card: c,
        normBack: normalizeHindiText(c.back || "")
      };
    });

    var result = {
      overall: { total: 0, targeted: 0, untargeted: 0, pct: 0 },
      verbs: { total: 0, targeted: 0, pct: 0, items: [] },
      nouns: { total: 0, targeted: 0, pct: 0, items: [] },
      adjectives: { total: 0, targeted: 0, pct: 0, items: [] },
      allItems: []
    };

    var categories = ["verbs", "nouns", "adjectives"];
    categories.forEach(function (cat) {
      var items = state.lexicon[cat] || [];
      result[cat].total = items.length;
      items.forEach(function (item) {
        var patterns = getWordPatterns(item.word, cat);
        var matchedCards = [];
        normCards.forEach(function (nc) {
          if (patterns.some(function (p) { return p.test(nc.normBack); })) {
            matchedCards.push(nc.card);
          }
        });

        var entry = {
          id: item.id,
          word: item.word,
          diacritics: item.diacritics || "",
          category: cat.slice(0, -1),
          catKey: cat,
          meaning: item.meaning || "",
          sample: item.sample || item.collocation || "",
          cardCount: matchedCards.length,
          matchedCards: matchedCards
        };

        if (matchedCards.length > 0) {
          result[cat].targeted++;
        }
        result[cat].items.push(entry);
        result.allItems.push(entry);
      });
      result[cat].pct = result[cat].total > 0 ? Math.round((result[cat].targeted / result[cat].total) * 100) : 0;
    });

    result.overall.total = result.allItems.length;
    result.overall.targeted = result.verbs.targeted + result.nouns.targeted + result.adjectives.targeted;
    result.overall.untargeted = result.overall.total - result.overall.targeted;
    result.overall.pct = result.overall.total > 0 ? Math.round((result.overall.targeted / result.overall.total) * 100) : 0;

    return result;
  }

  function renderLexiconStats() {
    var cov = computeLexiconCoverage();
    if (!cov) return;

    var statLexEl = document.getElementById("stat-lexicon");
    if (statLexEl) {
      statLexEl.textContent = cov.overall.targeted + "/" + cov.overall.total + " (" + cov.overall.pct + "%)";
      var descEl = document.getElementById("stat-lexicon-desc");
      if (descEl) {
        descEl.textContent = cov.verbs.targeted + "v · " + cov.nouns.targeted + "n · " + cov.adjectives.targeted + "adj";
      }
    }

    var badgeNavEl = document.getElementById("nav-lexicon-badge");
    if (badgeNavEl) {
      badgeNavEl.textContent = cov.overall.pct + "%";
    }

    var overviewBadge = document.getElementById("lex-overview-badge");
    if (overviewBadge) {
      overviewBadge.textContent = cov.overall.pct + "% Targeted";
    }

    var verbsVal = document.getElementById("lex-bar-verbs-val");
    if (verbsVal) verbsVal.textContent = cov.verbs.targeted + "/" + cov.verbs.total + " (" + cov.verbs.pct + "%)";
    var verbsFill = document.getElementById("lex-bar-verbs");
    if (verbsFill) verbsFill.style.width = cov.verbs.pct + "%";

    var nounsVal = document.getElementById("lex-bar-nouns-val");
    if (nounsVal) nounsVal.textContent = cov.nouns.targeted + "/" + cov.nouns.total + " (" + cov.nouns.pct + "%)";
    var nounsFill = document.getElementById("lex-bar-nouns");
    if (nounsFill) nounsFill.style.width = cov.nouns.pct + "%";

    var adjsVal = document.getElementById("lex-bar-adjs-val");
    if (adjsVal) adjsVal.textContent = cov.adjectives.targeted + "/" + cov.adjectives.total + " (" + cov.adjectives.pct + "%)";
    var adjsFill = document.getElementById("lex-bar-adjs");
    if (adjsFill) adjsFill.style.width = cov.adjectives.pct + "%";
  }

  function renderLexiconView() {
    var cov = computeLexiconCoverage();
    if (!cov) return;

    renderLexiconStats();

    var elOverall = document.getElementById("metric-lex-overall");
    if (elOverall) elOverall.textContent = cov.overall.pct + "%";
    var elOverallSub = document.getElementById("metric-lex-overall-sub");
    if (elOverallSub) elOverallSub.textContent = cov.overall.targeted + " of " + cov.overall.total + " targeted";

    var elVerbs = document.getElementById("metric-lex-verbs");
    if (elVerbs) elVerbs.textContent = cov.verbs.pct + "%";
    var elVerbsSub = document.getElementById("metric-lex-verbs-sub");
    if (elVerbsSub) elVerbsSub.textContent = cov.verbs.targeted + "/" + cov.verbs.total + " targeted";

    var elNouns = document.getElementById("metric-lex-nouns");
    if (elNouns) elNouns.textContent = cov.nouns.pct + "%";
    var elNounsSub = document.getElementById("metric-lex-nouns-sub");
    if (elNounsSub) elNounsSub.textContent = cov.nouns.targeted + "/" + cov.nouns.total + " targeted";

    var elAdjs = document.getElementById("metric-lex-adjs");
    if (elAdjs) elAdjs.textContent = cov.adjectives.pct + "%";
    var elAdjsSub = document.getElementById("metric-lex-adjs-sub");
    if (elAdjsSub) elAdjsSub.textContent = cov.adjectives.targeted + "/" + cov.adjectives.total + " targeted";

    var elUntargeted = document.getElementById("metric-lex-untargeted");
    if (elUntargeted) elUntargeted.textContent = cov.overall.untargeted;

    var items = [];
    if (state.lexiconCategory === "all") {
      items = cov.allItems;
    } else {
      items = cov[state.lexiconCategory] ? cov[state.lexiconCategory].items : [];
    }

    if (state.lexiconCoverageFilter === "untargeted") {
      items = items.filter(function (it) { return it.cardCount === 0; });
    } else if (state.lexiconCoverageFilter === "low") {
      items = items.filter(function (it) { return it.cardCount >= 1 && it.cardCount <= 2; });
    } else if (state.lexiconCoverageFilter === "covered") {
      items = items.filter(function (it) { return it.cardCount >= 3; });
    }

    if (state.lexiconSearchQuery && state.lexiconSearchQuery.trim() !== "") {
      var q = state.lexiconSearchQuery.toLowerCase().trim();
      items = items.filter(function (it) {
        return it.word.toLowerCase().indexOf(q) !== -1 ||
               it.diacritics.toLowerCase().indexOf(q) !== -1 ||
               it.meaning.toLowerCase().indexOf(q) !== -1 ||
               it.sample.toLowerCase().indexOf(q) !== -1;
      });
    }

    var tbody = document.getElementById("lexicon-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (items.length === 0) {
      var trEmpty = document.createElement("tr");
      trEmpty.innerHTML = '<td colspan="7" style="text-align: center; padding: 32px; color: var(--text-muted); font-size: 0.95rem;">No vocabulary anchors match your filter or search query.</td>';
      tbody.appendChild(trEmpty);
      return;
    }

    items.forEach(function (it) {
      var tr = document.createElement("tr");

      var badgeClass = "untargeted";
      var badgeText = "⚪ 0 cards";
      if (it.cardCount >= 3) {
        badgeClass = "covered";
        badgeText = "🟢 " + it.cardCount + " cards";
      } else if (it.cardCount > 0) {
        badgeClass = "low";
        badgeText = "🟡 " + it.cardCount + " card" + (it.cardCount > 1 ? "s" : "");
      }

      var actionHtml = it.cardCount > 0
        ? '<button class="btn btn-sm btn-secondary lex-view-cards-btn" style="padding: 4px 10px; font-size: 0.8rem;">View ' + it.cardCount + ' Cards</button>'
        : '<span style="color: var(--text-faint); font-size: 0.8rem;">Untargeted</span>';

      tr.innerHTML =
        '<td style="color: var(--text-faint); font-size: 0.82rem;">' + it.id + '</td>' +
        '<td>' +
          '<div class="lex-word-title">' + it.word + '</div>' +
          (it.diacritics ? '<div class="lex-word-diacritics">' + it.diacritics + '</div>' : '') +
        '</td>' +
        '<td><span class="lex-tag-pill ' + it.category + '">' + it.category + '</span></td>' +
        '<td style="color: #fff; font-weight: 500;">' + it.meaning + '</td>' +
        '<td><span class="lex-colloc">' + (it.sample || "—") + '</span></td>' +
        '<td style="text-align: center;">' +
          '<span class="lex-cov-badge ' + badgeClass + '" title="Click to view cards">' + badgeText + '</span>' +
        '</td>' +
        '<td style="text-align: right;">' + actionHtml + '</td>';

      if (it.cardCount > 0) {
        var badgeEl = tr.querySelector(".lex-cov-badge");
        if (badgeEl) {
          badgeEl.addEventListener("click", function () {
            openLexiconCardsModal(it);
          });
        }
        var btnEl = tr.querySelector(".lex-view-cards-btn");
        if (btnEl) {
          btnEl.addEventListener("click", function (e) {
            e.stopPropagation();
            openLexiconCardsModal(it);
          });
        }
      }

      tbody.appendChild(tr);
    });
  }

  function openLexiconCardsModal(item) {
    var modal = document.getElementById("lexicon-cards-modal");
    if (!modal) return;

    document.getElementById("lex-modal-title").textContent = "Cards Practicing: " + item.word + " (" + item.meaning + ")";
    document.getElementById("lex-modal-subtitle").textContent = "Found " + item.cardCount + " flashcard" + (item.cardCount > 1 ? "s" : "") + " in your Hindi Anki deck.";

    var list = document.getElementById("lex-modal-card-list");
    list.innerHTML = "";

    item.matchedCards.forEach(function (c) {
      var cardEl = document.createElement("div");
      cardEl.className = "candidate-card";

      var statusPill = "";
      if (c.status === "Mastered") {
        statusPill = '<span class="status-pill mastered" style="padding: 2px 8px; font-size: 0.72rem;">🟢 Mastered</span>';
      } else if (c.status === "Struggling") {
        statusPill = '<span class="status-pill struggling" style="padding: 2px 8px; font-size: 0.72rem;">🔴 Struggling</span>';
      } else {
        statusPill = '<span class="status-pill learning" style="padding: 2px 8px; font-size: 0.72rem;">🟡 Learning</span>';
      }

      var lessonTag = c.primary_lesson ? '<span class="peek-badge" style="font-size: 0.72rem; padding: 2px 8px;">' + c.primary_lesson + '</span>' : '';

      cardEl.innerHTML =
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">' +
          '<div style="display: flex; gap: 8px; align-items: center;">' +
            lessonTag +
            statusPill +
          '</div>' +
          '<span style="font-size: 0.75rem; color: var(--text-faint);">Interval: ' + (c.interval || 0) + 'd</span>' +
        '</div>' +
        '<div style="margin-bottom: 8px;">' +
          '<div style="font-size: 0.75rem; color: #60a5fa; font-weight: 700; text-transform: uppercase;">English Prompt</div>' +
          '<div style="font-size: 0.94rem; color: #fff; font-weight: 500;">' + c.front + '</div>' +
        '</div>' +
        '<div>' +
          '<div style="font-size: 0.75rem; color: #34d399; font-weight: 700; text-transform: uppercase;">Hindi Target &amp; Gloss</div>' +
          '<div style="font-size: 0.88rem; color: #e2e8f0; line-height: 1.5;">' + c.back + '</div>' +
        '</div>';

      list.appendChild(cardEl);
    });

    modal.style.display = "flex";
  }

  function closeLexiconCardsModal() {
    var modal = document.getElementById("lexicon-cards-modal");
    if (modal) modal.style.display = "none";
  }

  // --- SERVER BRIDGE & HEARTBEAT ENGINE ---
  async function checkServerHeartbeat() {
    var isHttp = (window.location.protocol.indexOf("http") === 0);
    if (!isHttp) {
      setExecutionMode(false);
      return;
    }
    try {
      var resp = await fetch("/api/heartbeat");
      if (resp.ok) {
        var data = await resp.json();
        setExecutionMode(!!data.live);
      } else {
        setExecutionMode(false);
      }
    } catch (e) {
      setExecutionMode(false);
    }
  }

  function setExecutionMode(isLive) {
    state.isServerLive = isLive;
    var banner = document.getElementById("mode-banner");
    var bannerText = document.getElementById("mode-banner-text");
    var badgeTag = document.getElementById("mode-badge-tag");

    if (!banner || !bannerText || !badgeTag) return;

    if (isLive) {
      banner.className = "mode-banner live";
      bannerText.innerHTML = "<b>Live Server Mode:</b> Connected to Python bridge (<code>run_dashboard.py</code>). Live Anki sync &amp; dynamic progress tracking active. (Auto-terminates when tab closes).";
      badgeTag.textContent = "⚡ Live Bridge";
      badgeTag.className = "mode-badge";
    } else {
      banner.className = "mode-banner static";
      bannerText.innerHTML = "<b>Static Snapshot Mode (file:///):</b> You opened index.html directly. Live Anki sync &amp; dynamic progress tracking require the Python server. Run <code>lessons-dashboard/run_dashboard.bat</code> for live mode.";
      badgeTag.textContent = "⚠️ Static Snapshot";
      badgeTag.className = "mode-badge";
    }
  }

  async function syncCurriculum(showFeedback) {
    if (state.isServerLive) {
      if (showFeedback) showToast("Checking progress.json and updating curriculum...");
      try {
        var resp = await fetch("/api/curriculum");
        if (resp.ok) {
          var freshLessons = await resp.json();
          if (Array.isArray(freshLessons) && freshLessons.length > 0) {
            state.curriculum = freshLessons;
            renderHeader();
            renderStats();
            handleRoute();
            var activeCode = (freshLessons.find(function (l) { return l.is_active; }) || {}).code || "A1-09";
            if (showFeedback) showToast("Curriculum updated! Active lesson: " + activeCode);
            return;
          }
        }
      } catch (e) {
        console.warn("Curriculum sync failed:", e);
      }
    } else {
      if (showFeedback) showToast("In static mode. Double-click run_dashboard.bat to sync with progress.json.");
    }
  }


  function renderCardGrid(cards, isGeneralView, isReferenceView) {
    const container = document.getElementById(isGeneralView ? "general-card-grid" : "detail-card-grid");
    container.innerHTML = "";

    if (isReferenceView) {
      container.innerHTML =
        '<div style="grid-column: 1/-1; padding: 36px 24px; text-align: center; color: #94a3b8; background: var(--bg-card); border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.3);">' +
          '<div style="font-size: 2.2rem; margin-bottom: 12px;">🎙️</div>' +
          '<h3 style="font-size: 1.25rem; color: #38bdf8; font-weight: 700; margin-bottom: 8px;">Foundational Phonetics Baseline</h3>' +
          '<p style="max-width: 650px; margin: 0 auto; line-height: 1.6; font-size: 0.95rem; color: #cbd5e1;">' +
            'Every single card across the entire Hindi Anki deck (<strong>182 cards</strong>) has phonetic diacritics included on the second line (macrons <i>ā, ī, ū</i> for long vowels and sub-dots <i>ṭ, ḍ, ṛ</i> for retroflexes). ' +
            'Because pronunciation is continuously reinforced across every card, <strong>dedicated Anki flashcards are not required for this lesson</strong>.' +
          '</p>' +
        '</div>';
      return;
    }

    let filtered = cards;
    if (state.cardFilter !== "all") {
      filtered = filtered.filter(function (c) {
        return c.status.toLowerCase() === state.cardFilter.toLowerCase();
      });
    }

    if (state.searchQuery.trim()) {
      const q = state.searchQuery.toLowerCase();
      filtered = filtered.filter(function (c) {
        return (c.front && c.front.toLowerCase().indexOf(q) !== -1) ||
               (c.back && c.back.toLowerCase().indexOf(q) !== -1);
      });
    }

    if (filtered.length === 0) {
      container.innerHTML =
        '<div style="grid-column: 1/-1; padding: 40px 20px; text-align: center; color: #94a3b8; background: var(--bg-card); border-radius: 12px; border: 1px dashed var(--border-subtle);">' +
          '<p style="font-size: 1.1rem; margin-bottom: 8px;">No cards found matching current filters.</p>' +
          '<p style="font-size: 0.85rem; color: #64748b;">Try adjusting your search query or status filter.</p>' +
        '</div>';
      return;
    }

    filtered.forEach(function (c) {
      const cardEl = document.createElement("div");
      cardEl.className = "anki-card status-" + c.status.toLowerCase();

      let statusPill = "";
      if (c.status === "Mastered") statusPill = '<span class="status-pill mastered">🟢 Mastered (' + c.interval + 'd)</span>';
      else if (c.status === "Learning") statusPill = '<span class="status-pill learning">🟡 Learning (' + c.interval + 'd)</span>';
      else statusPill = '<span class="status-pill struggling">🔴 Struggling (' + c.interval + 'd, ' + c.lapses + ' lapses)</span>';

      let lessonTagHtml = "";
      if (c.lesson_codes && c.lesson_codes.length > 0) {
        lessonTagHtml = c.lesson_codes.map(function (code) {
          return '<span class="peek-badge" style="font-size: 0.72rem; padding: 2px 8px;">' + code + '</span>';
        }).join(" ");
      }

      let focusHtml = "";
      if (c.target_focus) {
        focusHtml = '<div class="target-focus-pill">🎯 Focus: ' + c.target_focus + '</div>';
      }

      cardEl.innerHTML =
        '<div class="card-top">' +
          statusPill +
          '<div class="card-stats">' +
            '<span>Reps: ' + c.reps + '</span>' +
            '<span>•</span>' +
            '<span>Lapses: ' + c.lapses + '</span>' +
            '<span>•</span>' +
            '<span>Ease: ' + Math.round(c.factor / 10) + '%</span>' +
          '</div>' +
        '</div>' +
        focusHtml +
        '<div class="card-front">' + c.front + '</div>' +
        '<div class="card-back">' + c.back + '</div>' +
        '<div class="card-footer">' +
          '<div>' + lessonTagHtml + '</div>' +
          '<span>Note #' + c.noteId + '</span>' +
        '</div>';

      container.appendChild(cardEl);
    });
  }

  let toastTimer = null;
  function showToast(msg, duration) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toast.classList.remove("show");
    }, duration || 2800);
  }

  // --- ROUTER ---
  function navigateTo(hash) {
    window.location.hash = hash;
  }

  function handleRoute() {
    const hash = window.location.hash || "#overview";
    state.cardFilter = "all";
    state.searchQuery = "";

    document.querySelectorAll(".filter-tab").forEach(function (t) {
      t.classList.toggle("active", t.dataset.filter === "all");
    });
    document.querySelectorAll(".search-input").forEach(function (i) { i.value = ""; });

    // Update top-nav tabs active state
    document.querySelectorAll(".nav-tab").forEach(function (tab) {
      const target = tab.dataset.target;
      if (hash === "#" + target || (target === "overview" && (hash === "#overview" || hash === ""))) {
        tab.classList.add("active");
      } else if (target === "lexicon" && hash === "#lexicon") {
        tab.classList.add("active");
      } else {
        tab.classList.remove("active");
      }
    });

    const curriculumState = computeCurriculumState();

    if (hash === "#overview" || hash === "") {
      state.activeView = "overview";
      document.getElementById("view-overview").className = "view-container active";
      document.getElementById("view-lesson-detail").className = "view-container";
      document.getElementById("view-general").className = "view-container";
      var viewLex = document.getElementById("view-lexicon");
      if (viewLex) viewLex.className = "view-container";

      renderProgressionBanner(curriculumState);
      renderGeneralSection(curriculumState);
      renderCurriculumList(curriculumState);
      renderLexiconStats();
    } else if (hash === "#general") {
      state.activeView = "general";
      document.getElementById("view-overview").className = "view-container";
      document.getElementById("view-lesson-detail").className = "view-container";
      document.getElementById("view-general").className = "view-container active";
      var viewLex = document.getElementById("view-lexicon");
      if (viewLex) viewLex.className = "view-container";

      renderGeneralView(curriculumState);
    } else if (hash === "#lexicon") {
      state.activeView = "lexicon";
      document.getElementById("view-overview").className = "view-container";
      document.getElementById("view-lesson-detail").className = "view-container";
      document.getElementById("view-general").className = "view-container";
      var viewLex = document.getElementById("view-lexicon");
      if (viewLex) viewLex.className = "view-container active";

      renderLexiconView();
    } else if (hash.indexOf("#lesson/") === 0) {
      const code = hash.replace("#lesson/", "");
      if (!curriculumState.unlockedCodes.has(code)) {
        showToast("Lesson " + code + " is locked! Notion page has not been created yet.");
        navigateTo("#overview");
        return;
      }
      state.activeView = "lesson";
      state.activeLessonCode = code;
      document.getElementById("view-overview").className = "view-container";
      document.getElementById("view-lesson-detail").className = "view-container active";
      document.getElementById("view-general").className = "view-container";
      var viewLex = document.getElementById("view-lexicon");
      if (viewLex) viewLex.className = "view-container";

      renderLessonDetail(code, curriculumState);
    }
  }

  // --- SYNC ENGINE ---
  async function triggerSync() {
    showToast("Syncing with AnkiConnect...");
    
    // 1. If running under local HTTP server, use server's /api/sync endpoint
    if (window.location.protocol.indexOf("http") === 0) {
      try {
        const resp = await fetch("/api/sync");
        if (resp.ok) {
          const fresh = await resp.json();
          state.cards = fresh.cards || [];
          state.isLive = true;
          state.syncedAt = fresh.synced_at;
          renderHeader();
          renderStats();
          handleRoute();
          showToast("Live Anki deck synced successfully (" + state.cards.length + " cards)!");
          return;
        }
      } catch (e) {
        console.warn("Backend /api/sync failed, attempting direct AnkiConnect fetch...");
      }
    }

    // 2. Direct browser AnkiConnect fetch (http://127.0.0.1:8765)
    try {
      const ctrl = new AbortController();
      const tid = setTimeout(function () { ctrl.abort(); }, 2000);
      const testResp = await fetch("http://127.0.0.1:8765", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "deckNames", version: 6 }),
        signal: ctrl.signal
      });
      clearTimeout(tid);

      if (testResp.ok) {
        // Fetch cards from AnkiConnect
        const fResp = await fetch("http://127.0.0.1:8765", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "findCards", version: 6, params: { query: 'deck:"Hindi"' } })
        });
        const fData = await fResp.json();
        if (fData.result && fData.result.length > 0) {
          const cResp = await fetch("http://127.0.0.1:8765", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "cardsInfo", version: 6, params: { cards: fData.result } })
          });
          const cData = await cResp.json();
          if (cData.result) {
            // Success
            state.isLive = true;
            state.syncedAt = new Date().toISOString();
            renderHeader();
            showToast("Connected to live Anki desktop!");
            return;
          }
        }
      }
    } catch (err) {
      console.warn("Direct AnkiConnect blocked by browser CORS:", err);
    }

    // 3. Inform user how to sync if blocked
    showToast("Running on cached snapshot. Run 'python run_dashboard.py' for live syncing!");
  }

  // --- CARD GENERATION MODAL CONTROLLER ---
  let activeModalCards = [];
  let activeModalLesson = null;
  let activeModalLessonTitle = null;

  function updateModalBaselineStatus() {
    const curState = computeCurriculumState();
    const lData = curState.lessonMap[activeModalLesson];
    const currentCount = lData ? lData.cards.length : 0;
    const deficit = Math.max(0, MIN_CARDS_PER_LESSON - currentCount);

    const badge = document.getElementById("modal-baseline-status");
    if (!badge) return;

    if (deficit > 0) {
      badge.className = "modal-baseline-badge";
      badge.innerHTML = "🎯 Deck: <b>" + currentCount + "/5</b> cards &bull; ⚠️ <b>Needs " + deficit + " more card" + (deficit > 1 ? "s" : "") + "</b> to reach baseline";
    } else {
      badge.className = "modal-baseline-badge met";
      badge.innerHTML = "🟢 Deck: <b>" + currentCount + "</b> cards &bull; <b>Baseline Satisfied</b> (Generating extra practice)";
    }
  }

  function openCardGenerationModal(lessonCode, lessonTitle, curriculumState) {
    activeModalLesson = lessonCode;
    activeModalLessonTitle = lessonTitle;
    const modal = document.getElementById("card-gen-modal");
    if (!modal) return;

    // Span title across width without lesson code badge
    document.getElementById("modal-title").textContent = "✨ Generate Cards for " + lessonCode + ": " + lessonTitle;
    document.getElementById("modal-subtitle").textContent = "Review candidate cards below. Click 'Add' to push individual cards directly to Anki, or 'Add All' to queue all visible cards.";

    // Existing fronts in deck to guarantee live novelty
    const existingFronts = new Set(state.cards.map(function (c) { return (c.front || "").toLowerCase().trim(); }));

    // Fetch candidates from bank
    const bank = (window.CARD_CANDIDATES && window.CARD_CANDIDATES[lessonCode]) ? window.CARD_CANDIDATES[lessonCode] : [];

    // Filter by novelty against current live state
    let availableBank = bank.filter(function (c) {
      return !existingFronts.has(c.front.toLowerCase().trim());
    });

    if (availableBank.length === 0) {
      availableBank = generateDynamicFallbackCards(lessonCode, lessonTitle, existingFronts);
    }

    // Determine how many cards to show:
    // If lesson is in deficit (< 5 cards), show EXACTLY the deficit count! (e.g. 1 for A1-03, 5 for A0-07)
    // If lesson already met baseline, default to 3 cards.
    const lData = curriculumState.lessonMap[lessonCode];
    const currentCount = lData ? lData.cards.length : 0;
    const deficit = Math.max(0, MIN_CARDS_PER_LESSON - currentCount);
    const countToShow = deficit > 0 ? deficit : Math.min(3, availableBank.length);

    activeModalCards = [];
    for (let i = 0; i < countToShow; i++) {
      const candidate = availableBank[i % availableBank.length];
      activeModalCards.push({
        id: "cand-" + i,
        front: candidate.front,
        back: candidate.back,
        lesson: lessonCode,
        target_focus: candidate.target_focus || ("[" + lessonCode + "] " + lessonTitle),
        isAdded: false,
        bankIndex: i
      });
    }

    renderModalCardList();
    updateModalBaselineStatus();
    modal.style.display = "flex";
  }

  function closeCardGenerationModal() {
    const modal = document.getElementById("card-gen-modal");
    if (modal) modal.style.display = "none";
  }

  function renderModalCardList() {
    const container = document.getElementById("modal-card-list");
    if (!container) return;
    container.innerHTML = "";

    if (activeModalCards.length === 0) {
      container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 30px;">All candidate cards for this lesson have been added to your Anki deck!</div>';
      return;
    }

    activeModalCards.forEach(function (card, index) {
      const tile = document.createElement("div");
      tile.className = "candidate-card-tile" + (card.isAdded ? " added" : "");
      tile.id = "tile-" + card.id;

      const header = document.createElement("div");
      header.className = "candidate-card-header";

      const meta = document.createElement("div");
      meta.className = "candidate-card-meta";
      meta.innerHTML = 
        '<span class="candidate-badge">Card #' + (index + 1) + '</span>' +
        '<span id="status-' + card.id + '" class="' + (card.isAdded ? "status-badge-added" : "status-badge-pending") + '">' +
          (card.isAdded ? "✓ Added to Anki" : "⚡ Ready to Add") +
        '</span>';

      const actions = document.createElement("div");
      actions.className = "candidate-actions";

      // Add Button
      const addBtn = document.createElement("button");
      addBtn.type = "button";
      if (card.isAdded) {
        addBtn.className = "action-pill btn-added";
        addBtn.textContent = "✓ Added";
        addBtn.disabled = true;
      } else {
        addBtn.className = "action-pill btn-add";
        addBtn.textContent = "+ Add";
        addBtn.onclick = function () {
          handleIndividualAdd(card, tile, addBtn, regenBtn);
        };
      }

      // Regenerate Button
      const regenBtn = document.createElement("button");
      regenBtn.type = "button";
      regenBtn.className = "action-pill btn-regen";
      regenBtn.textContent = "↻ Regenerate";
      if (card.isAdded) {
        regenBtn.style.display = "none";
      } else {
        regenBtn.onclick = function () {
          handleIndividualRegenerate(card, tile, index);
        };
      }

      actions.appendChild(addBtn);
      actions.appendChild(regenBtn);

      header.appendChild(meta);
      header.appendChild(actions);

      const contentGrid = document.createElement("div");
      contentGrid.className = "candidate-content-grid";

      const frontBox = document.createElement("div");
      frontBox.className = "candidate-box";
      frontBox.innerHTML = 
        '<div class="candidate-box-label candidate-front-label">Front (English Prompt)</div>' +
        '<div class="candidate-front-text">' + card.front + '</div>';

      const backBox = document.createElement("div");
      backBox.className = "candidate-box";
      backBox.innerHTML = 
        '<div class="candidate-box-label candidate-back-label">Back (Hinglish Answer & Breakdown)</div>' +
        '<div class="candidate-back-text">' + card.back + '</div>';

      contentGrid.appendChild(frontBox);
      contentGrid.appendChild(backBox);

      tile.appendChild(header);
      tile.appendChild(contentGrid);
      container.appendChild(tile);
    });

    updateAddAllButtonState();
  }

  async function handleIndividualAdd(card, tile, addBtn, regenBtn) {
    if (card.isAdded) return;

    addBtn.disabled = true;
    addBtn.textContent = "Connecting...";

    const payload = [{
      front: card.front,
      back: card.back,
      lesson: activeModalLesson
    }];

    try {
      const result = await sendCardsToAnki(payload);
      if (result && result.success && result.addedCount > 0) {
        card.isAdded = true;
        tile.className = "candidate-card-tile added";
        addBtn.className = "action-pill btn-added";
        addBtn.textContent = "✓ Added";
        if (regenBtn) regenBtn.style.display = "none";

        const statusBadge = tile.querySelector("#status-" + card.id);
        if (statusBadge) {
          statusBadge.className = "status-badge-added";
          statusBadge.textContent = "✓ Added to Anki";
        }

        const noteId = (result.noteIds && result.noteIds[0]) ? result.noteIds[0] : Date.now();
        state.cards.push({
          cardId: noteId,
          noteId: noteId,
          front: card.front,
          back: card.back,
          interval: 0,
          reps: 0,
          lapses: 0,
          queue: 0,
          factor: 2500,
          status: "Learning",
          tags: ["hindi-coach", "lesson::" + activeModalLesson],
          primary_lesson: activeModalLesson,
          target_focus: card.target_focus,
          all_matched_lessons: [activeModalLesson],
          lesson_codes: [activeModalLesson],
          is_general: false
        });

        updateModalBaselineStatus();
        updateAddAllButtonState();

        const curState = computeCurriculumState();
        renderStats();
        renderProgressionBanner(curState);
        renderCurriculumList(curState);
        if (state.activeView === "lesson" && state.activeLessonCode === activeModalLesson) {
          renderLessonDetail(activeModalLesson, curState);
        }

        showToast("✨ Card successfully added to Anki deck!");
      } else {
        addBtn.disabled = false;
        addBtn.textContent = "+ Add";
        const errMsg = (result && result.error) ? result.error : "Failed to connect to Anki.";
        showToast("❌ " + errMsg, 4500);
      }
    } catch (err) {
      addBtn.disabled = false;
      addBtn.textContent = "+ Add";
      showToast("❌ " + (err.message || "Failed to reach Anki Desktop"), 4500);
    }
  }

  const DEFAULT_GEMINI_KEY = "";

  function getGeminiApiKey() {
    return localStorage.getItem("hindi_coach_gemini_api_key") || DEFAULT_GEMINI_KEY;
  }

  function setGeminiApiKey(key) {
    if (key && key.trim()) {
      localStorage.setItem("hindi_coach_gemini_api_key", key.trim());
    } else {
      localStorage.removeItem("hindi_coach_gemini_api_key");
    }
  }

  async function generateCardWithGemini(lessonCode, lessonTitle, existingFrontsList) {
    const apiKey = getGeminiApiKey();
    if (!apiKey) return null;

    const url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key=" + encodeURIComponent(apiKey);

    const systemInstruction = 
      "You are Diya, an expert personal Hindi language coach for a male polyglot in Toronto (AI professional, plays guitar/piano, friend Shivani in Norwich UK).\n" +
      "Generate 1 novel Anki flashcard for the specified lesson.\n" +
      "STRICT RULES:\n" +
      "1. Return ONLY valid JSON with keys: 'front', 'back', 'target_focus'.\n" +
      "2. 'front': Natural English sentence with speaker/listener gender or formality markers in parentheses, e.g. (casual, m) or (informal, f).\n" +
      "3. 'back': MUST have exactly 4 sections separated by <br><br>:\n" +
      "   - Section 1: Natural Romanized Hindi (NO Devanagari script). Male self-reference uses -taa / gayaa / karungaa.\n" +
      "   - Section 2: <span style=\"color: #718096;\"><i>Romanized Hindi with phonetic diacritics (macrons: ā, ī, ū; retroflexes: ṭ, ḍ, ṛ)</i></span>\n" +
      "   - Section 3: <span style=\"color: #2b6cb0;\"><small>Word-by-word gloss separated by vertical bars (|)</small></span>\n" +
      "   - Section 4: <span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [" + lessonCode + "] Grammar explanation</small></span>\n" +
      "4. NEVER use Devanagari script anywhere.\n" +
      "5. Avoid any of the following already existing sentences:\n" + existingFrontsList.slice(0, 15).join("; ");

    const userPrompt = "Lesson: " + lessonCode + " - " + lessonTitle + ". Generate 1 fresh, natural conversational practice sentence.";

    const payload = {
      contents: [{ parts: [{ text: userPrompt }] }],
      systemInstruction: { parts: [{ text: systemInstruction }] },
      generationConfig: {
        responseMimeType: "application/json",
        temperature: 0.75
      }
    };

    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (resp.ok) {
        const data = await resp.json();
        const candidateText = data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts && data.candidates[0].content.parts[0] && data.candidates[0].content.parts[0].text;
        if (candidateText) {
          const parsed = JSON.parse(candidateText);
          if (parsed.front && parsed.back) {
            return {
              front: parsed.front,
              back: parsed.back,
              target_focus: parsed.target_focus || ("[" + lessonCode + "] " + lessonTitle),
              isAiGenerated: true
            };
          }
        }
      } else {
        console.warn("Gemini API call returned status:", resp.status);
      }
    } catch (e) {
      console.warn("Gemini generation error:", e);
    }
    return null;
  }

  async function handleIndividualRegenerate(card, tile, cardIndex) {
    const existingFronts = new Set(state.cards.map(function (c) { return (c.front || "").toLowerCase().trim(); }));
    // Also consider cards already visible in modal
    activeModalCards.forEach(function (c) {
      if (c.id !== card.id) existingFronts.add(c.front.toLowerCase().trim());
    });

    const regenBtn = tile.querySelector(".btn-regen");
    if (regenBtn) {
      regenBtn.disabled = true;
      regenBtn.textContent = "↻ Generating...";
    }

    let nextCandidate = null;

    // 1. Attempt live Gemini API generation
    try {
      const aiCard = await generateCardWithGemini(activeModalLesson, activeModalLessonTitle, Array.from(existingFronts));
      if (aiCard && !existingFronts.has(aiCard.front.toLowerCase().trim())) {
        nextCandidate = aiCard;
      }
    } catch (aiErr) {
      console.warn("AI generation attempt failed, using novel bank fallback:", aiErr);
    }

    // 2. Fallback to candidate bank if Gemini is unavailable
    if (!nextCandidate) {
      const bank = (window.CARD_CANDIDATES && window.CARD_CANDIDATES[activeModalLesson]) ? window.CARD_CANDIDATES[activeModalLesson] : [];
      for (let i = 1; i <= bank.length; i++) {
        const idx = (card.bankIndex + i) % bank.length;
        const cand = bank[idx];
        if (!existingFronts.has(cand.front.toLowerCase().trim())) {
          nextCandidate = cand;
          card.bankIndex = idx;
          break;
        }
      }
    }

    if (!nextCandidate) {
      const fallbacks = generateDynamicFallbackCards(activeModalLesson, activeModalLessonTitle, existingFronts);
      nextCandidate = fallbacks[Math.floor(Math.random() * fallbacks.length)];
    }

    card.front = nextCandidate.front;
    card.back = nextCandidate.back;
    card.target_focus = nextCandidate.target_focus || ("[" + activeModalLesson + "] " + activeModalLessonTitle);

    // Update tile contents
    const frontText = tile.querySelector(".candidate-front-text");
    const backText = tile.querySelector(".candidate-back-text");
    if (frontText) frontText.innerHTML = card.front;
    if (backText) backText.innerHTML = card.back;

    // Trigger visual refresh animation
    tile.classList.remove("fade-in-refresh");
    void tile.offsetWidth;
    tile.classList.add("fade-in-refresh");

    if (regenBtn) {
      regenBtn.disabled = false;
      regenBtn.textContent = "↻ Regenerate";
    }

    if (nextCandidate.isAiGenerated) {
      showToast("⚡ AI Generated Card #" + (cardIndex + 1) + " via Gemini!");
    } else {
      showToast("↻ Regenerated Card #" + (cardIndex + 1));
    }
  }

  async function handleAddAllVisible() {
    const unadded = activeModalCards.filter(function (c) { return !c.isAdded; });
    if (unadded.length === 0) return;

    const addAllBtn = document.getElementById("modal-add-all-btn");
    if (addAllBtn) {
      addAllBtn.disabled = true;
      addAllBtn.textContent = "Connecting to Anki...";
    }

    const payload = unadded.map(function (c) {
      return {
        front: c.front,
        back: c.back,
        lesson: activeModalLesson
      };
    });

    try {
      const result = await sendCardsToAnki(payload);
      if (result && result.success && result.addedCount > 0) {
        for (let i = 0; i < result.addedCount; i++) {
          const c = unadded[i];
          if (!c) break;
          c.isAdded = true;
          const noteId = (result.noteIds && result.noteIds[i]) ? result.noteIds[i] : (Date.now() + i);
          state.cards.push({
            cardId: noteId,
            noteId: noteId,
            front: c.front,
            back: c.back,
            interval: 0,
            reps: 0,
            lapses: 0,
            queue: 0,
            factor: 2500,
            status: "Learning",
            tags: ["hindi-coach", "lesson::" + activeModalLesson],
            primary_lesson: activeModalLesson,
            target_focus: c.target_focus,
            all_matched_lessons: [activeModalLesson],
            lesson_codes: [activeModalLesson],
            is_general: false
          });
        }

        renderModalCardList();
        updateModalBaselineStatus();

        const curState = computeCurriculumState();
        renderStats();
        renderProgressionBanner(curState);
        renderCurriculumList(curState);
        if (state.activeView === "lesson" && state.activeLessonCode === activeModalLesson) {
          renderLessonDetail(activeModalLesson, curState);
        }

        showToast("✨ Added " + result.addedCount + " cards to Anki deck!");
      } else {
        if (addAllBtn) {
          addAllBtn.disabled = false;
          addAllBtn.textContent = "➕ Add All (" + unadded.length + ") to Anki";
        }
        const errMsg = (result && result.error) ? result.error : "Failed to connect to Anki.";
        showToast("❌ " + errMsg, 4500);
      }
    } catch (err) {
      if (addAllBtn) {
        addAllBtn.disabled = false;
        addAllBtn.textContent = "➕ Add All (" + unadded.length + ") to Anki";
      }
      showToast("❌ " + (err.message || "Failed to reach Anki Desktop"), 4500);
    }
  }

  async function handleRegenerateAllVisible() {
    const unaddedIndices = [];
    activeModalCards.forEach(function (c, idx) {
      if (!c.isAdded) unaddedIndices.push(idx);
    });
    if (unaddedIndices.length === 0) return;

    const regenAllBtn = document.getElementById("modal-regen-all-btn");
    if (regenAllBtn) {
      regenAllBtn.disabled = true;
      regenAllBtn.textContent = "↻ Generating...";
    }

    for (const idx of unaddedIndices) {
      const c = activeModalCards[idx];
      const tile = document.getElementById("tile-" + c.id);
      if (tile) {
        await handleIndividualRegenerate(c, tile, idx);
      }
    }

    if (regenAllBtn) {
      regenAllBtn.disabled = false;
      regenAllBtn.textContent = "↻ Regenerate All";
    }
    showToast("↻ Regenerated all un-added cards!");
  }

  function updateAddAllButtonState() {
    const addAllBtn = document.getElementById("modal-add-all-btn");
    if (!addAllBtn) return;
    const unadded = activeModalCards.filter(function (c) { return !c.isAdded; });
    if (unadded.length === 0) {
      addAllBtn.disabled = true;
      addAllBtn.textContent = "✓ All Cards Added";
      addAllBtn.style.opacity = "0.6";
    } else {
      addAllBtn.disabled = false;
      addAllBtn.textContent = "➕ Add All (" + unadded.length + ") to Anki";
      addAllBtn.style.opacity = "1";
    }
  }

  async function sendCardsToAnki(cardsPayload) {
    const isFileProtocol = window.location.protocol === "file:";

    // Helper for direct AnkiConnect call
    async function tryDirectAnkiConnect() {
      try {
        const notes = cardsPayload.map(function (c) {
          const tags = ["hindi-coach"];
          if (c.lesson) tags.push("lesson::" + c.lesson);
          return {
            deckName: "Hindi",
            modelName: "Basic",
            fields: {
              "Front": c.front,
              "Back": c.back
            },
            options: {
              allowDuplicate: false,
              duplicateScope: "deck"
            },
            tags: tags
          };
        });

        const ankiResp = await fetch("http://127.0.0.1:8765", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "addNotes",
            version: 6,
            params: { notes: notes }
          })
        });

        if (ankiResp.ok) {
          const ankiData = await ankiResp.json();
          if (ankiData.error) {
            return { success: false, error: "AnkiConnect error: " + ankiData.error };
          }
          if (ankiData.result && Array.isArray(ankiData.result)) {
            const validIds = ankiData.result.filter(function (id) { return id !== null; });
            if (validIds.length > 0) {
              return {
                success: true,
                addedCount: validIds.length,
                noteIds: validIds,
                source: "direct"
              };
            } else {
              return {
                success: false,
                error: "Anki rejected cards as duplicates. Click 'Regenerate' to create novel cards."
              };
            }
          }
        }
      } catch (directErr) {
        // Direct attempt failed, let fallback proceed
      }
      return null;
    }

    // Helper for backend bridge call
    async function tryBridge(url) {
      try {
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cards: cardsPayload })
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.success && data.added_count > 0 && data.note_ids && data.note_ids.length > 0) {
            return {
              success: true,
              addedCount: data.added_count,
              noteIds: data.note_ids,
              source: "bridge"
            };
          }
          if (data.queued_count > 0 && data.added_count === 0) {
            return {
              success: false,
              error: "Anki Desktop is not running. Make sure Anki is open with AnkiConnect enabled."
            };
          }
        }
      } catch (e) {
        // Continue fallback
      }
      return null;
    }

    // When running directly from file:///, attempt direct AnkiConnect first (CORS-friendly, no port 8080 noise)
    if (isFileProtocol) {
      const directRes = await tryDirectAnkiConnect();
      if (directRes) return directRes;

      const bridgeRes = await tryBridge("http://localhost:8080/api/add-cards");
      if (bridgeRes) return bridgeRes;
    } else {
      // Under http://localhost:8080, try relative bridge first, then direct
      const bridgeUrls = ["/api/add-cards", "http://localhost:8080/api/add-cards"];
      for (const bUrl of bridgeUrls) {
        const bridgeRes = await tryBridge(bUrl);
        if (bridgeRes) return bridgeRes;
      }

      const directRes = await tryDirectAnkiConnect();
      if (directRes) return directRes;
    }

    return {
      success: false,
      error: "Could not connect to Anki desktop (127.0.0.1:8765). Please make sure Anki is open with AnkiConnect installed, or run 'python run_dashboard.py'."
    };
  }

  function generateDynamicFallbackCards(lessonCode, lessonTitle, existingFronts) {
    return [
      {
        front: "Let's review the main grammar concept of this lesson together. (<i>informal, m</i>)",
        back: "Chalo is lesson ke core grammar concept ko ek saath review karte hain.<br><br><span style=\"color: #718096;\"><i>Chalo is lesson ke core grammar concept ko ek sāth review karte haiṁ.</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Chalo (let's) | is lesson ke concept ko (this lesson's concept - oblique) | ek sāth (together) | review karte haiṁ (review)</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [" + lessonCode + "] " + lessonTitle + "</small></span>",
        target_focus: "[" + lessonCode + "] " + lessonTitle
      }
    ];
  }

  // --- INIT ---
  function init() {
    // 1. Load Curriculum Data
    if (window.CURRICULUM_DATA && Array.isArray(window.CURRICULUM_DATA)) {
      state.curriculum = window.CURRICULUM_DATA;
    } else {
      console.error("window.CURRICULUM_DATA not found. Please ensure data/curriculum_data.js is loaded.");
    }

    // 2. Load Deck Snapshot Data
    if (window.DECK_SNAPSHOT && window.DECK_SNAPSHOT.cards) {
      state.cards = window.DECK_SNAPSHOT.cards;
      state.syncedAt = window.DECK_SNAPSHOT.synced_at;
      state.isLive = false;
    } else {
      console.error("window.DECK_SNAPSHOT not found. Please ensure data/snapshot_data.js is loaded.");
    }

    // 3. Load High-ROI Lexicon Data
    if (window.HIGH_ROI_LEXICON) {
      state.lexicon = window.HIGH_ROI_LEXICON;
    }

    // 4. Render immediately
    renderHeader();
    renderStats();
    renderLexiconStats();
    handleRoute();

    // 5. Server heartbeat & live vs static mode check
    checkServerHeartbeat();
    setInterval(checkServerHeartbeat, 3000);

    // Watchdog beacon on browser/tab close
    window.addEventListener("beforeunload", function () {
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/api/shutdown");
      }
    });

    // Check for updated curriculum from progress.json on startup
    syncCurriculum(false);

    // 6. Attach listeners
    window.addEventListener("hashchange", handleRoute);

    const refreshBtn = document.getElementById("refresh-btn");
    if (refreshBtn) refreshBtn.addEventListener("click", triggerSync);

    const syncCurriculumBtn = document.getElementById("sync-curriculum-btn");
    if (syncCurriculumBtn) {
      syncCurriculumBtn.addEventListener("click", function () {
        syncCurriculum(true);
      });
    }

    // Top Navigation Tabs
    document.querySelectorAll(".nav-tab").forEach(function (tab) {
      tab.addEventListener("click", function () {
        navigateTo("#" + tab.dataset.target);
      });
    });

    // Lexicon Stat Card click
    const statCardLex = document.getElementById("stat-card-lexicon");
    if (statCardLex) {
      statCardLex.addEventListener("click", function () {
        navigateTo("#lexicon");
      });
    }

    // Overview section Lexicon button
    const openLexBtn = document.getElementById("open-lexicon-btn");
    if (openLexBtn) {
      openLexBtn.addEventListener("click", function () {
        navigateTo("#lexicon");
      });
    }

    // Lexicon Category Filter Tabs
    const lexCatTabs = document.getElementById("lexicon-cat-tabs");
    if (lexCatTabs) {
      lexCatTabs.querySelectorAll(".filter-tab").forEach(function (btn) {
        btn.addEventListener("click", function () {
          state.lexiconCategory = btn.dataset.cat;
          lexCatTabs.querySelectorAll(".filter-tab").forEach(function (b) { b.classList.remove("active"); });
          btn.classList.add("active");
          renderLexiconView();
        });
      });
    }

    // Lexicon Coverage Dropdown Filter
    const lexCoverageFilter = document.getElementById("lexicon-coverage-filter");
    if (lexCoverageFilter) {
      lexCoverageFilter.addEventListener("change", function (e) {
        state.lexiconCoverageFilter = e.target.value;
        renderLexiconView();
      });
    }

    // Lexicon Search Input
    const lexSearchInput = document.getElementById("lexicon-search-input");
    if (lexSearchInput) {
      lexSearchInput.addEventListener("input", function (e) {
        state.lexiconSearchQuery = e.target.value;
        renderLexiconView();
      });
    }

    // Lexicon Modal Close Buttons
    const lexModalCloseBtn = document.getElementById("lex-modal-close-btn");
    if (lexModalCloseBtn) lexModalCloseBtn.addEventListener("click", closeLexiconCardsModal);

    const lexModalCancelBtn = document.getElementById("lex-modal-cancel-btn");
    if (lexModalCancelBtn) lexModalCancelBtn.addEventListener("click", closeLexiconCardsModal);

    const lexModal = document.getElementById("lexicon-cards-modal");
    if (lexModal) {
      lexModal.addEventListener("click", function (e) {
        if (e.target === lexModal) closeLexiconCardsModal();
      });
    }

    const genCardSec = document.getElementById("general-card-section");
    if (genCardSec) {
      genCardSec.addEventListener("click", function () {
        navigateTo("#general");
      });
    }

    // Modal listeners
    const closeBtn = document.getElementById("modal-close-btn");
    if (closeBtn) closeBtn.addEventListener("click", closeCardGenerationModal);

    const cancelBtn = document.getElementById("modal-cancel-btn");
    if (cancelBtn) cancelBtn.addEventListener("click", closeCardGenerationModal);

    const addAllBtn = document.getElementById("modal-add-all-btn");
    if (addAllBtn) addAllBtn.addEventListener("click", handleAddAllVisible);

    const regenAllBtn = document.getElementById("modal-regen-all-btn");
    if (regenAllBtn) regenAllBtn.addEventListener("click", handleRegenerateAllVisible);

    const geminiConfigBtn = document.getElementById("modal-gemini-config-btn");
    if (geminiConfigBtn) {
      geminiConfigBtn.addEventListener("click", function () {
        const curKey = getGeminiApiKey();
        const masked = curKey ? (curKey.slice(0, 6) + "..." + curKey.slice(-4)) : "None";
        const newKey = window.prompt("Gemini API Key for Live Card Generation:\n(Stored safely in your browser's localStorage)\n\nCurrent Key: " + masked + "\n\nEnter new key or leave blank to keep current:", "");
        if (newKey !== null && newKey.trim() !== "") {
          setGeminiApiKey(newKey.trim());
          showToast("🔑 Gemini API key updated in localStorage!");
        }
      });
    }

    const modalBackdrop = document.getElementById("card-gen-modal");
    if (modalBackdrop) {
      modalBackdrop.addEventListener("click", function (e) {
        if (e.target === modalBackdrop) closeCardGenerationModal();
      });
    }

    document.querySelectorAll(".filter-tab").forEach(function (btn) {
      if (btn.closest("#lexicon-cat-tabs")) return;
      btn.addEventListener("click", function (e) {
        state.cardFilter = e.target.dataset.filter;
        document.querySelectorAll(".filter-tab").forEach(function (b) {
          if (!b.closest("#lexicon-cat-tabs")) b.classList.remove("active");
        });
        e.target.classList.add("active");

        const curState = computeCurriculumState();
        if (state.activeView === "lesson") {
          const l = curState.lessonMap[state.activeLessonCode];
          renderCardGrid(l ? l.cards : [], false);
        } else if (state.activeView === "general") {
          renderGeneralView(curState);
        }
      });
    });

    document.querySelectorAll(".search-input").forEach(function (inp) {
      if (inp.id === "lexicon-search-input") return;
      inp.addEventListener("input", function (e) {
        state.searchQuery = e.target.value;
        const curState = computeCurriculumState();
        if (state.activeView === "lesson") {
          const l = curState.lessonMap[state.activeLessonCode];
          renderCardGrid(l ? l.cards : [], false);
        } else if (state.activeView === "general") {
          renderGeneralView(curState);
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
