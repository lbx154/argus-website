# Get Started External Video Picker Implementation Plan

> **For agentic workers:** Implement task-by-task with TDD and independent review.

**Goal:** Move the four-run selector outside the CLI frame and turn it into a prominent horizontal poster rail.

**Architecture:** `ResearchVideoDemo.astro` owns the external picker, CLI frame, and player as one interaction component. `start.astro` supplies section placement only; shared CSS owns desktop four-card layout and mobile snap scrolling.

**Tech Stack:** Astro 5, semantic HTML, CSS, dependency-free TypeScript browser script, existing bilingual build contract.

## Global Constraints

- Preserve all four existing sources, posters, labels, and download behavior.
- Selector renders before and outside `.demo-frame`.
- Desktop shows four poster cards; narrow widths use horizontal scroll snap.
- Mobile cards are about 82vw and reveal the next card.
- Selected state includes blue-gold border and text badge.
- Keyboard tab behavior and panel labeling remain valid.
- Reduced motion disables forced smooth scroll and auto-play.
- No page-level horizontal overflow.
- Preserve existing user changes in `src/pages/index.astro` and unrelated `global.css` hunks.

---

### Task 1: External film picker component

**Files:**
- Modify: `src/components/ResearchVideoDemo.astro`
- Modify: `src/pages/start.astro`
- Modify: `src/styles/global.css`
- Modify: `scripts/check-bilingual.mjs`

- [ ] Write a failing build contract that asserts each built Start page has:
  - `data-run-picker`;
  - four `data-video-src` cards;
  - picker before `.demo-frame`;
  - no `.cli-demo-tabs` inside `.demo-frame`;
  - `data-run-category`, `data-run-duration`, and `data-now-playing`;
  - mobile snap CSS and selected blue-gold border tokens.

- [ ] Run `npm run build` and confirm it fails on missing `data-run-picker`.

- [ ] Refactor `ResearchVideoDemo.astro`:
  - extend each run with category, duration, pacing, and CTA copy;
  - render heading + horizontal poster rail;
  - render cards with poster backgrounds and decorative play controls;
  - render the CLI `.demo-frame terminal-demo` after the rail;
  - keep one tabpanel and existing source-switching behavior;
  - scroll player into view only for pointer/keyboard activation on desktop;
  - keep IntersectionObserver auto-play rules.

- [ ] Remove the outer `.demo-frame` and frame bar from `start.astro`.
  Change hero primary link to `#run-picker`.

- [ ] Replace old tab CSS with film picker CSS:
  - four-column desktop rail;
  - poster overlay, badge, play button, result title, metadata;
  - selected gradient-border pseudo-element and `NOW PLAYING`;
  - mobile horizontal rail with mandatory snap, 82vw cards, edge fades, and hint;
  - visible focus ring and reduced-motion overrides.

- [ ] Run `npm run build`.

- [ ] Verify `/start.html` and `/zh/start.html` at 1440, 1024, 390, and 320:
  - no page overflow;
  - four cards;
  - selecting card 4 changes the video source and panel label;
  - keyboard arrows and Home/End work;
  - card 4 can be reached by mobile horizontal scrolling;
  - reduced motion does not auto-play or smooth-scroll.

- [ ] Commit source and tests only, then rebase and push.

