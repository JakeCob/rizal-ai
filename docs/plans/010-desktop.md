# Plan 010: Tablet and desktop layouts

Workflow phases 0 to 5. Status: complete. Date: 2026-09-26. Same setup as plan 008 (builder, reviewer, architect as tester; deploys to Vercel from the CLI).

Scope, grilled with the owner on 2026-09-26 after seeing production on a desktop: real layouts at the tablet (768px) and desktop (1024px) breakpoints on every screen, with the phone layout byte-identical. Tree: three columns above 1024px (a slim units nav, the path with wider spacing and bigger nodes, a progress column with streak, XP, hearts and the next lesson), two columns (nav and path) between 768 and 1023. Lesson runner, practice and end screens: one centered reading column up to 720px, larger vignette type and line height on desktop, tile banks wrapping in the wider row, the Check and Continue bar as a bottom bar inside the column, the completion passages card as two columns. Keyboard shortcuts (1 to 9 pick tiles in bank order, Backspace removes the last, Enter checks or continues) with a hint on wide screens. This supersedes plan 009's column-only framing (D38).

## Phase 0: Setup

### Analysis

The 448px wrapper in app/layout.tsx is the only width cap and every route shares it; plan 009 framed it above md. Tailwind's default md (48rem) and lg (64rem) match the chosen breakpoints. The tree page holds the two queries the new columns need (tree and me), and the API marks at most one active lesson, so the next-lesson card is the active lesson or an all-done state; no new request (D14). The runner scrolls the window, its footer is viewport-fixed and centered, and plan 006's scroll contract and plan 009's frame clip depend on that, so the footer stays fixed and takes the frame's exact max width. The gloss sheet's width lives in unlayered CSS. Dark mode is class-based and dormant (nothing adds the class), so new tokens go in both blocks and no dark behavior is claimed. Landscape phones hit md, so widths change at md and the type scale only at lg. Test fixtures pin several names (one Start link, one footer, one status region, one heading with RizalAI, the Total XP and Streak labels), so new desktop DOM avoids those names and uses landmarks (nav, main, aside) and a definition list for stats.

Lead calls: the 768 to 1023 split is nav plus path (stats stay in the header); keys are 1 to 9 only; no programmatic focus moves; the keyboard listeners stay on at every width; dark mode activation is a separate owner decision (tech debt row).

### Behaviors

Phone gate:
- Given the iPhone Playwright project, when the six screens spec screenshots are taken before and after this plan, then their sha256 hashes are unchanged, and every existing iPhone spec (200ms check, scroll spec) stays green.

Tree:
- Given 1280x800, when the tree renders, then a units nav, the path in a main landmark and a progress aside are visible left to right without overlap, nodes are at least 88px, the progress column shows streak, XP and hearts as a definition list, the next-lesson card names the active lesson and links to it with a link named "Go to lesson", and there is no horizontal overflow.
- Given 768x1024, when the tree renders, then the nav and the path are visible, the aside is hidden, and the header stats remain.
- Given every lesson done, when the tree renders on desktop, then the next-lesson card shows an all-done state.
- Given a nav link, when clicked, then the page scrolls to that unit's heading (smooth only under motion-safe).

Runner, practice and end screens:
- Given 1280x800, when a lesson is played, then the column is at most 720px and centered, vignette lines have a computed font size of at least 22px with a line-height ratio of at least 1.5, the footer and the feedback sheet stay inside the column and the footer ends at the frame's bottom edge, the gloss sheet stays inside the column, and the completion card shows the passage section and the reflection region side by side.
- Given 768x1024, when a lesson is played, then the frame sits inside the viewport, the footer stays inside it, and the phone type scale applies.
- Given the practice page with due items on desktop, when it renders, then it mirrors the runner's column and its footer is clipped to the frame like the runner's.
- Given the out-of-hearts screen on desktop, when it renders, then its CTA stays inside the column.

Keyboard:
- Given an exercise with a tile bank, when digit N is pressed, then the Nth unused bank tile is picked; Backspace removes the last picked tile; Enter checks when an answer exists; Enter on the feedback sheet continues; Enter on a vignette beat advances it.
- Given a multiple-choice exercise, when digit N is pressed, then option N is chosen; Enter checks.
- Given a focused button or link, when Enter is pressed, then native activation runs once and no attempt is posted twice (a focused radio option is the exception: Enter checks).
- Given the gloss sheet open, when Enter is pressed, then nothing advances.
- Given 1280x800, when a tile bank renders, then a hint "1 to 9 picks a word, Backspace removes, Enter checks" is visible and is not a live region; on the iPhone project it is hidden.

### Phases of work and parallelism

- A. Runner, practice, end screens, and the frame contract (builder): layout.tsx width classes with the data-layout attribute, globals.css sheet width, runner and end screen classes, practice mirror and footer clip, playwright.config projects (tablet added, matches adjusted), desktop.spec rewritten, tablet.spec. Reviewer reviews.
- B. Tree (builder, after A because A lands the frame contract): page grid, SkillTree and PathNode responsive classes, UnitNav, ProgressPanel, NextLessonCard, lib/tree/summary with tests, desktop-tree.spec. Reviewer reviews.
- C. Keyboard (builder, after B): shortcuts module and hook with tests, wiring in ExerciseView, Runner and practice, hint and badges, desktop-keyboard.spec. Reviewer reviews.
- D. Architect: verify each handoff (Vitest, lint, typecheck, all Playwright projects, phone screenshot hashes), docs (this plan, D38, README, tech debt, rollback), commits, push, CLI deploy, production check at 1280x800 and on the phone viewport.

### File ownership

| Worker | Files |
|---|---|
| builder (A) | apps/web/app/layout.tsx, app/globals.css, playwright.config.ts, components/runner/Runner.tsx, VignettePlayer.tsx, ExerciseView.tsx (classes only), TileBank.tsx (sizes only), components/card/ReflectionCard.tsx, app/practice/page.tsx, app/lesson/[id]/page.tsx, e2e/desktop.spec.ts, e2e/tablet.spec.ts (new) |
| builder (B) | apps/web/app/page.tsx, components/tree/SkillTree.tsx, PathNode.tsx, UnitNav.tsx (new), ProgressPanel.tsx (new), NextLessonCard.tsx (new), lib/tree/summary.ts and test (new), components/tree/SkillTree.test.tsx, e2e/desktop-tree.spec.ts (new) |
| builder (C) | lib/runner/shortcuts.ts and test (new), components/runner/useShortcuts.ts and test (new), wiring in ExerciseView.tsx, Runner.tsx, app/practice/page.tsx, hint and badges in TileBank.tsx, e2e/desktop-keyboard.spec.ts (new) |
| reviewer | reads everything, edits nothing |
| architect | this plan, DECISIONS.md, apps/web/README.md, docs/tech-debt.md, docs/rollback.md |

## Phase 1: Document

Tech debt: new row, dark mode is class-based and never activated, so the dark tokens (including the desktop background) never apply; activating it by prefers-color-scheme changes phones and is an owner decision. Rollback: revert the commits and redeploy from the CLI; the phone layout is unchanged by construction, so a partial revert of one task is safe.

## Phase 2: TDD plan

Red first on each task: desktop.spec's existing width assertion (at most 448px) is the natural red for A once the frame widens; tablet.spec and the new desktop assertions fail on today's layout; desktop-tree.spec fails without the landmarks and the card; the shortcuts unit tests and desktop-keyboard.spec fail without the hook. Green per task, then Vitest, lint, typecheck, all Playwright projects, and the phone screenshot hash comparison recorded in each report.

### Checklist

- [x] A. Runner, practice, end screens, frame contract, tablet project: builder, reviewer
- [x] B. Tree three columns and two columns, nav, progress panel, next-lesson card: builder, reviewer
- [x] C. Keyboard shortcuts with hint: builder, reviewer
- [x] D. Architect: verify, docs, D38, commits, push, deploy, production check

## Phase 3 record

Three builder tasks in sequence (runner and frame, tree, keyboard), each reviewed, each with a fix round, plus a polish round on the tree. Findings: the runner task grew some type at md instead of lg, its footer checks could not catch a narrower footer, the fixed bars could exceed the frame beside a classic scrollbar, and the tablet spec missed the likeliest breaks; all fixed, and the exercise body is now vertically balanced from md while the frame's side borders continue beside the footer. The tree task was MERGE first time; its polish round aligned the nav with the wordmark, made the desktop zigzag symmetric, gave the unit progress a visible track with the current unit marked, and centralised the frame width in one custom property. The keyboard task had one real bug: Enter on a focused but unchosen option graded the previous choice, which could cost a heart; fixed by claiming Enter on a radio only when it is already chosen, with a unit test and a Playwright step. Phone byte-identity held on every task, checked by screenshot hashes with the Next dev badge masked (the only pixels that differ between any two dev runs).

Operational: two agents running Playwright in the same web folder collided twice (a dev server on port 3000 from a scratch config, a trace file removed mid-run); recorded on the board as a rule to serialise, and a fixed mock port for the scratch configs is the fix.

Results at the end of the plan:

| Suite | Result |
|---|---|
| Web Vitest | 122 passed (50 new), coverage 92.5 percent statements, lint and typecheck clean |
| Playwright | 12 passed across the iPhone, tablet and desktop projects; the 200ms and scroll checks stay on the iPhone project |
| Phone gate | six iPhone screenshots identical before and after every task with the dev badge masked |

Accepted as nits: the progress list's live region has no label of its own (its aside is labelled); the tile bank wrap can leave one tile alone on a row at 720px; tall pages scroll the frame's bottom edge away while the fixed footer stays.

## Phase 4: Review

- Commits: one for the web change (all three tasks and the polish, since they share files) and one for the docs; pushed; deployed to Vercel from the CLI.
- Docs: this plan, D38, apps/web/README.md wording, tech debt row 30 (dark mode dormant).
- Feature flag: none; the breakpoints are CSS.

## Phase 5: Retrospective

Design questions asked up front (three columns, reading column, shortcuts, breakpoints) kept the build to three tasks with no re-litigation. The phone-hash gate made a large layout change safe: every task proved the phone untouched. Reviews still found one behavior bug and four layout misses on first pass; for UI work the reviewer's screenshot walk (what a user sees at each width) found what the assertions did not, so keep it in every UI brief. Next: the owner's phone and desktop play-throughs of production, then the audio bake-off (tech debt 14) or Unit 3 content.
