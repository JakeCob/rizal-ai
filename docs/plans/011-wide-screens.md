# Plan 011: Full-bleed layout on wide screens

Workflow phases 0 to 5. Status: complete. Date: 2026-09-26. Same setup as plan 010.

Scope, chosen by the owner on 2026-09-26 after seeing plan 010 on a wide monitor: from 1280px (xl) the card frame goes away. The app background fills the viewport, the tree's nav and progress columns stay fixed-width and sticky, and the path column stretches between them up to a total cap of about 1600px; the lesson runner, practice and end screens keep their 720px centered reading column on the plain app background. Tablets (768 to 1279px) keep the card frame from plans 009 and 010. Phone byte-identical.

## Phase 0: Setup

### Analysis

The frame is the layout wrapper's md classes (border, rounded corners, shadow, column background) plus the body's desk background, with the width in the --frame-w custom property and the data-layout="wide" variants at lg (max-w-6xl). The fixed footer and the gloss sheet track --frame-w. At xl the wrapper drops the frame classes and the body background matches the app background; the tree grid gets a wider cap and a fluid center column; the runner keeps its column. The desktop Playwright project runs at 1280x800, which is exactly the xl breakpoint, so a new "wide" project at 1920x1080 proves the full-bleed layout and the desktop project keeps proving the 1280 state (which is now full-bleed too, since xl starts at 1280).

### Behaviors

- Given a viewport of 1920x1080, when the tree renders, then there is no card border or shadow, the body background equals the app background, the nav and progress columns are fixed-width and sticky, the path column spans the remaining width up to a 1600px total, and there is no horizontal overflow.
- Given 1920x1080, when a lesson is played, then the reading column is 720px centered on the app background, the footer bar tracks the column, and the feedback and gloss sheets stay inside it.
- Given 1024x768 (tablet, below xl), when the tree and a lesson render, then the card frame from plan 010 is unchanged.
- Given the iPhone project, when the screens spec runs, then the screenshot hashes are unchanged (dev badge masked).

### File ownership

| Worker | Files |
|---|---|
| builder | apps/web/app/layout.tsx, app/globals.css, app/page.tsx (grid cap and xl classes), components/runner/Runner.tsx and app/practice/page.tsx (footer xl classes only), playwright.config.ts (a "wide" project at 1920x1080), e2e/wide.spec.ts (new), desktop.spec.ts and desktop-tree.spec.ts (assertions that assumed the frame at 1280) |
| reviewer | reads everything, edits nothing |
| architect | this plan, deploy |

## Phase 2: TDD plan

Red first: wide.spec.ts at 1920x1080 asserting no border and no shadow on the wrapper, body background equal to the app background, the three tree columns with the center column wider than 600px, the runner column at 720px centered; fails on the current framed layout. Green: xl classes and the tree cap. Then Vitest, lint, typecheck, all Playwright projects, and the phone hash gate.

### Checklist

- [x] A. Full-bleed from xl with a wide Playwright project: builder, reviewer
- [x] B. Architect: verify, commit, push, deploy, production check at 1920 and 1280

## Phase 3 record

One builder task, one review, one fix round, re-check MERGE. The first review found that the tablet spec never asserted the card and that the path column shrank from 510px to 464px when a window crossed 1280 (the body gutters stayed while the xl grid grew its side columns); fixed by keeping the lg column widths at xl and moving the wider set to 1536px, with a spec that measures main at 1279 and 1280. Visual notes fixed: the path band is capped inside the fluid column so the zigzag stays with its banner, the header carries a rule at xl, the exercise takes a top bias on tall screens instead of pure centering, and the bars carry a top border and shadow so they read as page bars on the plain background. Phone hashes identical; the tablet card unchanged and now asserted. Architect: 122 Vitest, 16 Playwright specs across iPhone, tablet, desktop and wide.

## Phase 4: Review

One web commit and one docs commit, pushed, deployed from the CLI.

## Phase 5: Retrospective

A breakpoint change is a width-function change: the review's arithmetic across the boundary (1279 versus 1280) caught what no single-viewport screenshot could. Every new breakpoint should get a "monotonic width" assertion.
