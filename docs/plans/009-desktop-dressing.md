# Plan 009: Dress the desktop around the phone column

Workflow phases 0 to 5. Status: complete. Date: 2026-09-26. Same setup as plan 008.

Scope, chosen by the owner on 2026-09-26 after seeing production on a desktop browser: keep the single phone-width column on every screen (mobile-first, D28 references) and make it read as intentional on wide screens: a page background and a subtle frame around the column above the tablet breakpoint, with the phone experience unchanged.

## Phase 0: Setup

### Analysis

apps/web/app/layout.tsx wraps every page in `mx-auto flex min-h-dvh w-full max-w-md flex-col` on a `min-h-dvh` body, so on a wide viewport the 448px column sits on the bare page background with no edge. The runner's footer is `fixed inset-x-0 bottom-0 mx-auto w-full max-w-md`, so it already stays inside the column. Colors and fonts come from tokens in app/globals.css. Nothing else is viewport-specific.

### Behaviors

- Given a viewport narrower than 768px, when any page renders, then the DOM and the visible layout are unchanged (Playwright iPhone screenshots stay the same; the 200ms and scroll checks pass).
- Given a viewport of 1280x800, when the tree, a lesson and the practice page render, then the column is centered, framed by a border and soft shadow with rounded corners, on a page background distinct from the column, and the fixed footer stays inside the column's edges.
- Given prefers-color-scheme dark, when the page renders, then the background and frame use the dark tokens.
- Given the column frame, when a lesson is played at 1280x800, then no element overflows the column and the gloss sheet and feedback sheet stay inside it.

### File ownership

| Worker | Files |
|---|---|
| builder | apps/web/app/layout.tsx, apps/web/app/globals.css, apps/web/components/runner/Runner.tsx (footer edge only if needed), apps/web/e2e/screens.spec.ts (a desktop project or a second viewport), apps/web/playwright.config.ts (a desktop project) |
| reviewer | reads everything, edits nothing |
| architect | this plan, deploy |

## Phase 1: Document

Tech debt: none new. Rollback: revert the commit and redeploy.

## Phase 2: TDD plan

Red first: a Playwright test on a desktop project (Desktop Chrome, 1280x800) asserting the column's bounding box is centered with a width at or under 448px and that its computed border and box-shadow are set, and that the runner footer's box stays within the column; it fails on today's layout because there is no frame. Green: the layout classes and tokens. Then `pnpm test && pnpm lint && pnpm typecheck && pnpm test:e2e` (both projects).

### Checklist

- [x] A. Desktop frame and background, phone unchanged, desktop Playwright project: builder, reviewer
- [x] B. Architect: verify, commit, push, CLI deploy to Vercel, check on a desktop viewport

## Phase 3 record

One builder brief, one review, MERGE on first pass. Red: the desktop Playwright spec failed on the old layout on the border check and on the full-width fixed footer. Green: tokens for the page background and frame in light and dark, the wrapper framed above the md breakpoint with byte-identical mobile classes, the runner footer clipped to the frame's bottom edge on desktop, a desktop Playwright project scoped so the iPhone-only checks stay on the iPhone project, and a determinism fix in the screens spec so the iPhone screenshot hashes could be compared before and after (unchanged). Architect: 72 Vitest, lint and typecheck clean, 7 Playwright specs green on both projects.

## Phase 4: Review

One commit, pushed, deployed to Vercel from the CLI (the GitHub app is not yet installed on the personal account). No docs beyond this plan.

## Phase 5: Retrospective

A one-screen change still earned a red test that caught the full-width footer. Screenshot hash comparisons need a determinism pass first (animations, the dev badge); the screens spec now has one.
