"""
Visual Anki Card Preview Generator
Generates an interactive HTML preview widget for newly generated Anki cards,
allowing the student to visually inspect Front and Back simultaneously
and rapidly page through all cards in the batch before pushing to Anki.
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Anki Flashcard Preview</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
</head>
<body class="bg-transparent text-[var(--foreground)] antialiased p-3 font-sans">
  <div class="max-w-3xl mx-auto bg-[var(--card)] text-[var(--foreground)] border border-[var(--border)] rounded-2xl p-5 shadow-lg">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-[var(--border)] pb-3 mb-4">
      <div class="flex items-center space-x-2">
        <span class="text-xl">🎴</span>
        <h2 class="font-bold text-base text-[var(--foreground)]">Flashcard Verification Preview</h2>
        <span class="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-medium border border-blue-500/20">Hindi Deck</span>
      </div>
      <div class="flex items-center space-x-3">
        <div class="text-xs text-[var(--muted-foreground)] font-medium" id="card-counter">Card 1 of {total_cards}</div>
        <button id="view-mode-btn" onclick="toggleViewMode()" class="text-xs px-2.5 py-1 rounded-md border border-[var(--border)] bg-[var(--background)] hover:bg-[var(--accent)] transition font-medium">
          📋 View All
        </button>
      </div>
    </div>

    <!-- Paged Mode (Default) -->
    <div id="paged-container">
      {paged_elements}
    </div>

    <!-- All Cards List Mode (Toggled) -->
    <div id="all-container" style="display: none;" class="space-y-4 max-h-[550px] overflow-y-auto pr-1">
      {all_elements}
    </div>

    <!-- Navigation & Approval Status Bar -->
    <div id="nav-bar" class="flex items-center justify-between mt-4 pt-3 border-t border-[var(--border)] text-xs">
      <div class="flex items-center space-x-2">
        <button id="prev-btn" onclick="prevCard()" class="px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--background)] hover:bg-[var(--accent)] disabled:opacity-30 transition font-medium">← Previous</button>
        <button id="next-btn" onclick="nextCard()" class="px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--background)] hover:bg-[var(--accent)] disabled:opacity-30 transition font-medium">Next →</button>
        <span class="text-[var(--muted-foreground)] text-xs ml-2 italic">Use Left / Right arrow keys to cycle</span>
      </div>
      <div class="flex items-center space-x-2 text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 font-medium">
        <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>Say "Push" to add to Anki</span>
      </div>
    </div>
  </div>

  <script>
    let currentIndex = 0;
    const totalCards = {total_cards};
    let isAllView = false;

    function updatePagedView() {
      for (let i = 0; i < totalCards; i++) {
        const el = document.getElementById(`paged-card-${i}`);
        if (el) el.style.display = (i === currentIndex) ? 'block' : 'none';
      }
      document.getElementById('card-counter').innerText = `Card ${currentIndex + 1} of ${totalCards}`;
      document.getElementById('prev-btn').disabled = (currentIndex === 0);
      document.getElementById('next-btn').disabled = (currentIndex === totalCards - 1);
    }

    function prevCard() {
      if (currentIndex > 0) {
        currentIndex--;
        updatePagedView();
      }
    }

    function nextCard() {
      if (currentIndex < totalCards - 1) {
        currentIndex++;
        updatePagedView();
      }
    }

    function toggleViewMode() {
      isAllView = !isAllView;
      const pagedCon = document.getElementById('paged-container');
      const allCon = document.getElementById('all-container');
      const navBar = document.getElementById('nav-bar');
      const modeBtn = document.getElementById('view-mode-btn');

      if (isAllView) {
        pagedCon.style.display = 'none';
        allCon.style.display = 'block';
        navBar.querySelector('#prev-btn').style.display = 'none';
        navBar.querySelector('#next-btn').style.display = 'none';
        modeBtn.innerText = '📑 Single Card View';
      } else {
        pagedCon.style.display = 'block';
        allCon.style.display = 'none';
        navBar.querySelector('#prev-btn').style.display = 'inline-block';
        navBar.querySelector('#next-btn').style.display = 'inline-block';
        modeBtn.innerText = '📋 View All';
        updatePagedView();
      }
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (!isAllView) {
        if (e.key === 'ArrowLeft') prevCard();
        if (e.key === 'ArrowRight') nextCard();
      }
    });

    updatePagedView();
  </script>
</body>
</html>
"""

def generate_preview_html(cards, output_path):
    """
    Renders Front and Back simultaneously side-by-side or stacked in a clean card format.
    """
    paged_elements = []
    all_elements = []

    for idx, card in enumerate(cards):
        front_content = card.get("front", "")
        back_content = card.get("back", "")
        display_style = "block" if idx == 0 else "none"

        card_html = f"""
        <div class="border border-[var(--border)] rounded-xl bg-[var(--background)] p-4 shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-stretch">
            <!-- Front (English Prompt) -->
            <div class="flex flex-col justify-between border border-dashed border-[var(--border)] rounded-lg bg-[var(--card)]/50 p-4">
              <div>
                <div class="text-[11px] font-semibold tracking-wide uppercase text-blue-400 mb-2 flex items-center space-x-1">
                  <span>Front (Prompt)</span>
                </div>
                <div class="text-base font-medium text-[var(--foreground)] leading-relaxed">
                  {front_content}
                </div>
              </div>
              <div class="text-[10px] text-[var(--muted-foreground)] mt-3 pt-2 border-t border-[var(--border)]/40">
                English scenario & formality target
              </div>
            </div>

            <!-- Back (Hinglish Answer & Breakdown) -->
            <div class="flex flex-col justify-between border border-dashed border-[var(--border)] rounded-lg bg-[var(--card)]/50 p-4">
              <div>
                <div class="text-[11px] font-semibold tracking-wide uppercase text-emerald-400 mb-2 flex items-center space-x-1">
                  <span>Back (Answer & Breakdown)</span>
                </div>
                <div class="text-sm leading-relaxed text-[var(--foreground)]">
                  {back_content}
                </div>
              </div>
              <div class="text-[10px] text-[var(--muted-foreground)] mt-3 pt-2 border-t border-[var(--border)]/40">
                Spoken Hindi • Diacritics • Word breakdown
              </div>
            </div>
          </div>
        </div>
        """

        # Paged version
        paged_elements.append(f'<div id="paged-card-{idx}" style="display: {display_style};">{card_html}</div>')

        # All cards version
        all_elements.append(f'<div class="relative"><div class="text-xs font-semibold text-[var(--muted-foreground)] mb-1">Card #{idx + 1}</div>{card_html}</div>')

    html_content = (
        TEMPLATE
        .replace("{total_cards}", str(len(cards)))
        .replace("{paged_elements}", "\n".join(paged_elements))
        .replace("{all_elements}", "\n".join(all_elements))
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path

if __name__ == "__main__":
    # Test script run
    test_cards = [
        {
            "front": "Are you free to grab a quick coffee this afternoon? (<i>informal, m</i>)",
            "back": "Kyaa tum aaj dopahar ko quick coffee peene ke liye free ho?<br><br><span style=\"color: #718096;\"><i>Kyā tum āj dopahar ko quick coffee pīne ke liye free ho?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Kyā (question marker) | tum (you) | āj (today) | dopahar ko (in afternoon) | coffee pīne ke liye (for drinking coffee) | free ho (are free)</small></span>"
        },
        {
            "front": "How is your work going at the care home in Norwich? (<i>informal, m</i>)",
            "back": "Norwich ke care home mein tumhaara kaam kaisaa chal rahaa hai?<br><br><span style=\"color: #718096;\"><i>Norwich ke care home meiṁ tumhārā kām kaisā chal rahā hai?</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Norwich ke care home meiṁ (in Norwich care home) | tumhārā kām (your work) | kaisā (how) | chal rahā hai (is going / progressing)</small></span>"
        }
    ]
    out = generate_preview_html(test_cards, "preview/card_preview.html")
    print(f"Updated preview HTML at: {out}")
