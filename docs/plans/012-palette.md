# Plan 012: Philippine palette, the sun and banig motifs, system dark mode

Workflow phases 0 to 5. Status: complete. Date: 2026-09-26. Same setup as plan 011.

Scope, grilled with the owner on 2026-09-26: re-skin the web app with a tempered Philippine flag palette (primary a royal blue a shade darker than the indigo, accent and XP the flag's golden yellow, hearts and danger the flag's red, warm off-white pages with a sun-gold highlight, a green that sits with the yellow); one restrained motif (the flag's eight-ray sun as the star on active path nodes and behind the completion score, a fine banig woven-mat texture on the desktop page background); and dark mode switched from the dormant class to the system setting with a designed dark set (navy pages, gold accents). Layout unchanged on every width; colors change on phones by design, so the screenshot-hash gate becomes a layout gate plus a contrast test.

## Phase 0: Setup

### Analysis

The reader's map (scratchpad map-palette.md, carried into the briefs) found: three current light pairs already fail WCAG AA (white text on the green and red buttons, red hearts and error text on the page); five shadcn components still draw from the neutral default blocks so a token-only re-skin would leave the lesson popover and the gloss sheet white; the favicon is the stock Next icon; and the old phone gate had no code behind it. The dark variant is class-based and dormant. Accent gold can never be text on a light page (about 1.5:1), so the gold page text (XP, streak) gets its own token, distinct from the text-on-accent token used on fills. Progress fills use gold in dark because blue fails 3:1 on the navy track.

Lead calls: the hues come from the flag's own values converted to oklch and tempered in lightness and chroma; the dark set is one media block after the light block; Playwright keeps rendering light by default and the screens spec adds a dark loop; the gate is a JSON box snapshot of every element's rect and typography plus a skeleton screenshot with colors forced to black on white; a contrast test parses the tokens and asserts the pairs; hearts never sit on the primary blue; the wordmark stays text.

### Behaviors

Gate and contrast (Task A, lands before the re-skin so the baselines are the pre-012 layout):
- Given the six screens states on the iPhone project, when the layout spec runs, then each JSON snapshot of rects and typography matches its baseline with no update, and the dark-scheme snapshot equals the light one.
- Given the same states, when the skeleton screenshot (colors forced, motifs hidden, dev badge masked) is compared, then it matches the baseline.
- Given app/globals.css, when the contrast test runs, then every named text pair is at least 4.5 and every named non-text pair at least 3 in both schemes, every light token has a dark value and vice versa, and every --color-* mapping resolves; it fails on today's tokens for the three known pairs.

Palette (Task B):
- Given the new tokens, when the app renders in light, then the primary is the tempered flag blue, XP and streak text are the gold text token, active and done nodes and the highlight use the accent gold, hearts and the wrong sheet use the tempered red, the correct sheet the leaf green, and the popover and gloss sheet use the RizalAI tokens.
- Given a system in dark mode, when the app renders, then pages are navy, text is warm paper white, accents gold, and the layout snapshot equals light.
- Given the components, when scanned, then no hardcoded color remains outside the tokens except the allowlisted theme colors.

Motifs and assets (Task C):
- Given an active path node, when it renders, then the star is the eight-ray sun in accent gold at the same 24px box; given a completed lesson, when the end screen renders, then a large faint sun sits behind the score and not on the out-of-hearts screen; the layout snapshots are unchanged.
- Given a desktop or tablet viewport, when the page renders, then the body background carries the banig texture at under 1.15:1 contrast; never on the phone and never on the column.
- Given the manifest and icons, when fetched, then the favicon, the PWA icons (including a maskable one) and the Apple touch icon show the sun mark on the flag blue, the theme colors follow the scheme, and the service worker cache name is bumped.

### Phases of work and parallelism

- A. Gate and contrast tests (builder): e2e/layout.spec.ts with baselines from the current layout, the skeleton screenshot, lib/theme/contrast.ts and its test (red on today's three failing pairs), the no-hardcoded-colors scan (red on today's list). Reviewer reviews.
- B. Tokens and dark mode (builder, after A): globals.css tokens light and dark, the variant switch, popover and sheet and progress on tokens, hardcoded colors moved, role splits, layout.tsx theme colors and colorScheme, screens spec dark loop. Reviewer reviews with the gate.
- C. Motifs and assets (builder, after B): Sun component on nodes and the end screen, banig on the body, icon.svg redraw and PNGs plus maskable and Apple icon, favicon, manifest, service worker bump. Reviewer reviews with the gate.
- D. Architect: verify each task (Vitest, lint, typecheck, all Playwright projects, the gate), docs (this plan, D39, tech debt 30 closed, README), commits, push, CLI deploy, production check in light and dark.

### File ownership

| Worker | Files |
|---|---|
| builder (A) | apps/web/e2e/layout.spec.ts (new) and its snapshots, e2e/screens.spec.ts (dev badge mask), next.config.ts (devIndicators), lib/theme/contrast.ts and contrast.test.ts (new), lib/theme/no-hardcoded-colors.test.ts (new) |
| builder (B) | apps/web/app/globals.css, app/layout.tsx, components/ui/popover.tsx, sheet.tsx, progress.tsx, dialog.tsx, components/runner/Runner.tsx, VignettePlayer.tsx, components/tree/PathNode.tsx (class only), SkillTree.tsx, ProgressPanel.tsx, UnitNav.tsx, components/card/ReflectionCard.tsx, app/page.tsx, app/practice/page.tsx, e2e/screens.spec.ts (dark loop), playwright.config.ts if a dark project is added |
| builder (C) | components/motif/Sun.tsx (new) and test, components/tree/PathNode.tsx (icon swap), components/runner/Runner.tsx (end screen sun), app/layout.tsx (banig class), public/icon.svg, icon-192.png, icon-512.png, icon-maskable-512.png (new), app/icon.svg (new), app/apple-icon.png (new), app/favicon.ico (removed), public/manifest.json, public/sw.js |
| reviewer | reads everything, edits nothing |
| architect | this plan, DECISIONS.md, docs/tech-debt.md, apps/web/README.md |

## Phase 1: Document

Tech debt: closes 30 (dark mode). New: 31, the dimmed vignette history lines read 2.9:1 in light and 4:1 in dark, so the current-versus-history cue is uneven across schemes; a scheme-aware dim is the fix. Rollback: revert the commits and redeploy; the service worker's network-first cache picks up the old assets on the next load.

## Phase 2: TDD plan

A: generate the layout baselines and the skeleton screenshots on the current commit (the red step is the baseline itself; the spec must pass on the current commit and would fail on a layout change, proven by a one-off class tweak in a scratch copy); the contrast test is red on today's tokens (three pairs); the no-hardcoded scan is red on today's list. B and C: the gate must pass with no baseline update, and the contrast test goes green with the new tokens; screens spec produces light and dark images for the reviewer's eyes.

### Checklist

- [x] A. Layout gate, skeleton screenshot, contrast test, hardcoded-color scan: builder, reviewer
- [x] B. Tokens light and dark, dark-mode switch, component tokens, role splits, theme colors: builder, reviewer
- [x] C. Sun motif on nodes and completion, banig texture, icons, favicon, manifest, service worker: builder, reviewer
- [x] D. Architect: verify, docs, D39, commits, push, deploy, production check in light and dark
- [x] E. Owner-approved follow-up after the production check: ring gap on the sun, softer dark completion glow: builder, reviewer

## Phase 3 record

Three builder tasks in sequence, each reviewed with a fix round, plus a re-check each. Task A landed the gate first (a JSON snapshot of every element's rect and typography per screen, a skeleton screenshot with colors forced to black on white, the dark snapshot asserted equal to light) and the contrast test, which was red on 27 pairs of the shipped palette (the three known text failures among them) and green after the tokens landed. Task B applied the flag-derived tokens in light and a navy-and-gold dark set, switched the dark variant to the system setting, moved every hardcoded color to tokens and put the popover, gloss sheet and progress bar on tokens; the reader's proposal had one out-of-gamut value (the text-on-accent token), corrected by 0.01 chroma. Its review asked for an opaque base under the tinted feedback sheets so the contrast test models what is painted, and a scheme-aware ring on the dark active node; both applied. Task C added the eight-ray sun (on the active node and as a glow behind the completion score), the banig texture, the icon set with a maskable icon and an Apple touch icon, the manifest colors and a service worker bump; the gate's walker had to learn to record a motif that takes part in layout (the node's sun) while still skipping the absolutely positioned one, a five-line change with no snapshot update; the review moved the banig off the full-bleed widths (it leaked into the body gutters as two strips at 1280 and up) so it lives only around the tablet and desktop card, and asked for a bolder sun and a raised, brighter completion glow in dark. The tester (now a Claude Code agent) prepared a six-combination production play-through script during the plan and ran it after the deploy: every palette, motif, layout, timing and contrast check passed at three widths in both schemes, plus four card-width probes for the banig; the only red row was audio, which is null in production and predates this plan (tech debt 14). Two visual notes from the reviewer and the tester went to the owner and were approved as a follow-up task: the rays now start 0.6 units outside the disc so the mark reads as the flag's sun rather than an eight-pointed star (icons re-rendered from the same geometry), and the dark completion glow dropped from 80 to 60 percent with a radial mask in both schemes, which raised the worst text pair over it from 4.78 to 5.70 on the composite and 5.87 in pixels. The review found the reviewer's own Playwright wait loop had matched its own shell in every round, so its "waited for other runs" claims in 012-b to 012-c2 were not true; the runs themselves were clean or re-run alone.

Results at the end of the plan: 213 Vitest tests (contrast 68 pairs, hardcoded-color scan, motif and manifest tests), lint and typecheck clean, 18 Playwright specs across the iPhone, tablet, desktop and wide projects, the layout gate green with the pre-012 baselines untouched.

## Phase 4: Review

One web commit and one docs commit, pushed, deployed from the CLI; the tester's production run in light and dark at three widths is recorded in its report. A third web commit carries the sun follow-up (task E), deployed after the owner's go. Docs: this plan, D39, tech debt 30 closed and 31 added, the web README.

## Phase 5: Retrospective

Landing the gate before the change made a full re-skin safe: every task proved the layout untouched while every pixel changed color. The contrast test caught three shipped failures nobody had seen. Two reviews found what tests could not: the texture strips at the screen edges and the muddy dark glow, both from looking at screenshots as a user. Parallel Playwright runs still collide; a per-agent port and report folder is the next fix.
