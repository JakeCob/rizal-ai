# Plan 006: CORS, beat scrolling, the orders helper, and lesson 7 (Fishing)

Workflow phases 0 to 5. Status: complete. Date: 2026-09-25. Run by an architect session with two Herdr workers (builder, reviewer); the architect runs the suites and the play-throughs (the Cursor tester stays parked).

Scope, grilled with the owner on 2026-09-25: pay tech debt 24 (the API has no CORS middleware) and 25 (the runner does not scroll a newly revealed beat into view), add the order-enumeration helper the plan 005 retrospective asked for, then author lesson 7 from Noli chapter 23 (Fishing) to replace the last Unit 2 stub. No audio, no deployment, no RLS cleanup.

## Phase 0: Setup

### Analysis

CORS. main.py registers no middleware; every browser request to the API preflights (Authorization, Content-Type, X-Timezone) and OPTIONS returns 405, so only mock mode works in a browser. Web on Vercel and API on Railway are different origins. Owner's decision (D36): the browser keeps calling the API cross-origin; the API allows an exact list of origins from CORS_ORIGINS plus an optional CORS_ORIGIN_REGEX for Vercel preview hostnames; no Next rewrite. Bearer tokens only, so credentials stay off. Settings are scalar strings today and pydantic-settings JSON-decodes list fields from env, so the origins live in a comma-separated string with a derived list property, the active_database_url pattern.

Scroll. The runner root is min-h-dvh and main has no fixed height, so the document scrolls and nothing moves it when a beat is revealed; from beat 3 on the current line sits under the fixed footer. VignettePlayer unmounts during every exercise and remounts after, so the scroll must run on mount as well as on reveal. Fix: a ref on the aria-current li, scroll-margin below it for the footer, scrollIntoView block nearest (auto under prefers-reduced-motion, smooth otherwise), and an instant scroll to top when an exercise or the end screen mounts so the page never starts mid-scroll. jsdom lacks scrollIntoView and matchMedia; guards plus stubs. The mock lesson's four short beats do not show the bug at 390x664, so the Playwright test uses a shorter viewport and must fail before the fix.

Orders helper. A pure module enumerates, per token exercise, the orders the tiles can build so the reviewer only judges naturalness. A permutation rule where only clitics and particles move reaches 11 of the 25 alternates authored so far; phrase movement (kay Padre Damaso, sa amin) and bank substitutions (ba, kaya) reach 24 of 25 as opt-in flags. Sizes stay in the low thousands per exercise with the flags, tens to hundreds without; a cap and a closed-form count keep output bounded. cli.py is excluded from coverage, so the logic lives in content/orders.py with its own tests and the CLI is a thin subcommand.

Corpus. Chapter 23 is the same number in all three editions (LA PESCA, ANG PANGIGISDA, Fishing): es 160 paragraphs, tl 157 body (tl 82 and 84 are section-break markers, 161 a footnote header, 162 a footnote; never pin), en 115. es and tl run one to one for 1 to 80; Poblete folds es 102 into tl 103 and es 107 into tl 107 and drops es 125; the Spanish lacks Maria Clara's "if you had not come up" (tl 145, en 108). The full merge table is in the architect's scratchpad map and the reviewer's corpus-ch23.md.

Scene chosen by the owner: the cayman (es 108 to 147, tl 108 to 147, en 81 to 109). Leon feels the cayman in the corral; Sinang and Maria Clara react; the pilot jumps in with a rope; Ibarra offers the knife, then dives after him; the water turns red; both surface with the dead cayman; the pilot says he owes Ibarra his life. Speakers: Leon, Sinang, Maria Clara, Ibarra, Matandang bangkero, Piloto, narrator. Owner's rulings: the paragraph with Rizal's aside about Filipino women not swooning is pinned (it carries the dive) and the vignette skips that sentence; the pilot's label is Piloto in this lesson and Elias from chapter 24 on, a recorded exception to the same-label norm because the novel withholds the name until chapter 24 and every pinned edition says "the pilot". The blood line is stated plainly in one beat, as chapter 10's hanging was.

### Behaviors

CORS:
- Given CORS_ORIGINS unset, when the API starts, then the allowed origins are http://localhost:3000 and http://127.0.0.1:3000.
- Given CORS_ORIGINS " https://rizal.vercel.app/ ,https://b.example,", when settings load, then the origin list is the two trimmed origins without trailing slash.
- Given a preflight OPTIONS from an allowed origin for POST with authorization, content-type and x-timezone, when the API answers, then status 200, allow-origin echoes the origin, allow-methods is GET POST OPTIONS, the three headers are allowed, and no allow-credentials header is sent.
- Given a preflight from an unlisted origin, when the API answers, then no allow-origin header is present.
- Given CORS_ORIGIN_REGEX set to a pattern, when a preflight comes from an origin matching it, then it is allowed; unset, no regex applies.
- Given a simple GET /health with an allowed Origin, when the API answers, then allow-origin echoes the origin and Vary includes Origin.

Scroll:
- Given the runner reveals a beat, when the beat index changes or the vignette mounts, then scrollIntoView is called on the aria-current li with block nearest, and behavior auto when prefers-reduced-motion is set.
- Given an exercise or the end screen mounts after the vignette scrolled, when it renders, then the window is scrolled to the top instantly.
- Given a 375x400 viewport in mock mode, when each vignette Continue reveals a beat, then the current beat's bottom is at or above the footer's top (fails before the fix).
- Given the existing Check to result timing test, when the fix lands, then it still passes under 200ms.

Orders helper:
- Given lesson 2 ex6, when the helper runs, then the listed alternate is reachable and excluded from candidates; with accepted_orders stripped it appears and the unlisted count rises by one.
- Given lesson 2 ex3, when the helper runs by the mover rule, then zero candidates; with --phrases and orders stripped, the trailing-kay order is a candidate; with orders kept, both authored orders are reported as listed.
- Given lesson 5 ex4 with --max 10, when the helper runs, then 10 candidates print and the output says showing 10 of 1678.
- Given a duplicate mover, when candidate_count runs, then it equals the enumerated set size.
- Given a tl_to_en translate_line, when movers are chosen, then the English list applies.
- Given `rizalai orders <file> --key exN`, when run in-process, then it prints the report and exits 0; an unknown key exits non-zero.

Lesson 7:
- Given lesson 7 (noli-fishing), when the content tests run, then 8 beats, 8 to 10 exercises, 8 groups spanning the three editions, unique locators, no tl 23:82, 23:84 or rows past 23:160 pinned.
- Given every vignette line, when compared with tl 23:108 to 147 with the trap list, then none is Poblete respelled, with no exemption for short lines (tl 112, 123, 126 and 142 are the known collisions).
- Given the pinned refs, when the card renders, then the sagip group shows es 139 and 140, tl 138 and 139, en 103 and 104, and the vignette does not carry the swoon aside.
- Given the seed, when it runs, then lesson 7 replaces the chapter 23 stub and Unit 2 has three published lessons.

### Phases of work and parallelism

- A. CORS (builder): settings, middleware, tests, env examples, docs. Reviewer reviews with a red run.
- B. Scroll (builder, after A's report; web only): VignettePlayer effect and margin, Runner scroll-to-top, Vitest stubs and cases, Playwright short-viewport test shown red first.
- C. Orders helper (builder, after B; api only): content/orders.py, loader.load_lesson, cli subcommand with argv, tests.
- D. Lesson 7 (builder, after C, drafted in the scratchpad and copied in when green): content/units/02-san-diego/03-fishing.yaml, unit.yaml, stub deleted (owner approved replacing the last stub in the 005 grilling; confirm at the plan go). Reviewer audits with corpus-ch23.md and the helper.
- E. Architect after each handoff: suites, seed, em dash grep, play-through of lesson 7 at 375px, docs, commits (one per task, docs last), no push unless asked.

Dependencies: B after A's report (one builder). C after B. D after C. Reviews trail each task by one.

### File ownership

| Worker | Files |
|---|---|
| builder (A) | apps/api/src/rizalai/config.py, main.py, tests/integration/test_cors.py (new), tests/unit/test_config.py (new), .env.example (root), apps/api/.env.example, apps/web/.env.example (one note), docs/deploy.md, apps/api/README.md, apps/web/README.md |
| builder (B) | apps/web/components/runner/VignettePlayer.tsx, Runner.tsx, components/runner/Runner.test.tsx, vitest.setup.ts, e2e/lesson.spec.ts or a new e2e/scroll.spec.ts |
| builder (C) | apps/api/src/rizalai/content/orders.py (new), content/loader.py (load_lesson), cli.py, tests/unit/test_orders.py (new) |
| builder (D) | content/units/02-san-diego/03-fishing.yaml (new), unit.yaml, 03-placeholder.yaml (deleted) |
| reviewer | reads everything, writes reports to the architect's scratchpad, edits nothing |
| architect | this plan, DECISIONS.md, docs/tech-debt.md, docs/architecture.md, docs/rollback.md |

### Authoring norms (carried from plan 005, plus this plan)

All plan 005 norms apply. New: a character the source leaves unnamed keeps the source's name for him (Piloto) until the chapter that names him; record the exception in the file header. The reviewer runs the orders helper on every token exercise and judges its candidates before judging by hand.

## Phase 1: Document

Tech debt: this plan closes 24 and 25 (rows removed at merge). Rows 2 (RLS), 14 (audio) and 23 (content hash) stay open. New, found by the scroll reader and logged at merge: the feedback sheet's 300ms slide exceeds the 200ms budget while the test checks an attribute, not the animation; long banks and tall wrong-answer sheets can sit under the footer on short phones; neither footer pads env(safe-area-inset-bottom).

Rollback: revert the commits in reverse order. A CORS problem in production is also fixable by editing CORS_ORIGINS or CORS_ORIGIN_REGEX on Railway and redeploying. The scroll and helper commits revert cleanly. The lesson 7 commit reverts to the stub on re-seed.

## Phase 2: TDD plan

Red first on each side, output in the report.

A. tests/unit/test_config.py: default list; trimming and trailing slash; regex unset is None. tests/integration/test_cors.py with a bare client over create_app(): allowed preflight; unlisted origin has no allow-origin; regex-matched origin allowed when set; simple GET carries allow-origin and Vary. Green: cors_origins and cors_origin_regex settings with cors_origin_list property; CORSMiddleware registration; env examples and docs.
B. Runner.test.tsx: scrollIntoView spy on Element.prototype called with the current li and block nearest after Continue; the remount path after an exercise; behavior auto under a matchMedia stub; window.scrollTo top when an exercise mounts. Playwright: a separate test at 375x400 asserting the current beat sits above the footer after each Continue, shown red first. Green: VignettePlayer ref, scroll margin, effect; Runner scrollTo; setup stubs.
C. tests/unit/test_orders.py per the behaviors; one in-process CLI smoke test with capsys. Green: orders.py, load_lesson, subcommand, main(argv).
D. The content tests are the red bar; the reviewer's audit and the owner's read are the gate.

### Checklist

- [x] A. CORS with exact list plus optional regex, tests, env examples, deploy doc: builder, reviewer
- [x] B. Current beat scrolls into view, page resets to top on exercise mount, Vitest and Playwright tests: builder, reviewer
- [x] C. `rizalai orders` helper with mover rule, block mode, --bank and --phrases opt-ins, cap and count: builder, reviewer
- [x] D. Lesson 7, Fishing (noli-fishing, the cayman, groups lawa, buwaya, sino, talon, sundang, piloto, sagip, utang): builder, reviewer, owner read
- [x] E. Architect: suites, seed, play-through of lesson 7, docs (D36, tech debt 24 and 25 removed, new rows), commits on main

## Phase 3 record

Same setup as plan 005: builder and reviewer in Herdr, the architect running suites, migrations, seeds and play-throughs, exploration by four in-process readers (CORS surface, runner scroll, chapter 23 corpus, CLI home for the helper) and the reviewer's corpus prep with a Poblete trap list. Six owner decisions came out of grilling: exact origins plus an optional preview regex; the cayman scene; the swoon paragraph pinned with the aside kept out of the vignette; Piloto as the label until chapter 24; delete the last stub; add a Unit 3 horizon stub.

Review findings by task:
- A, CORS: MERGE with four should-fixes (a preview regex anyone could squat by naming a Vercel project, tests reading the developer's environment, blank regex normalized only in main.py, and 500s carrying no CORS headers, which became an operator note in docs/rollback.md), folded in and re-checked MERGE. Every positive test was shown red on HEAD and a live preflight was checked with curl. The builder also found that apps/web/.env.example had never been tracked because the web .gitignore matched it; fixed.
- B, scroll: FIX on first review for a real ordering bug: the scroll-to-top effect on exerciseIndex also fired when the index returned to null and, because React runs a child's effects before its parent's, cancelled the beat scroll on the remount after every exercise. StrictMode's double effects hid it in dev; the reviewer proved it with a call-order probe and the builder proved it red against a production build. Fixed by moving the scroll-to-top into mount effects of ExerciseView and EndScreen, re-checked MERGE.
- C, orders helper: FIX on first review because the opt-in flags were intersected rather than united and a bank-added particle could not move in block mode, plus six should-fixes (listed orders above the limit, count labelling, listen_tap noise, frozen fixtures instead of live content, CLI checks). Fixed, re-checked MERGE, orders.py at 100 percent coverage.
- D, lesson 7: the builder stopped at the copy step because the content test demanded at least one unpublished stub and lesson 7 replaced the last one; the architect relaxed the guard, landed the draft, and the owner chose a Unit 3 horizon stub. The reviewer's audit of the draft was MERGE with two should-fixes (pin es/tl 23:117 and es 23:138 / tl 23:137 for symmetric cards; "buhay na buwaya") and a rephrased b7 opening away from Poblete's frame, applied. No D01 hit on the hardest short-line chapter so far; the orders helper ran on every token exercise before review.

Owner gate on 2026-09-25: lesson 7 read and approved.

Results at the end of the plan:

| Suite | Result |
|---|---|
| API pytest | 207 passed, 88.3 percent coverage, ruff and mypy strict clean |
| Web Vitest | 72 passed, lint and typecheck clean |
| Playwright e2e | 4 passed on the iPhone project incl. the 200ms check; the scroll spec at 375x330 red on a production build of the old code, green now |
| Seed on the dev database | 3 units, 8 lessons, 70 exercises, 0 unresolved refs (lesson 7: 37 refs in 8 groups) |
| Play-through of lesson 7 at 375px | Plain Chromium (no web-security flag) through the web app against the real API after completing lessons 1 to 6 through the API: 8 nodes on the tree, 0 console errors, 0 CORS failures, preflights captured with the expected allow headers and no credentials; lesson 7 played end to end, 3 alternates graded correct, 1 deliberate wrong answer with the red sheet and one heart, 90 XP; Check to result max 10 ms median 7 ms, Continue to next screen max 29 ms median 16 ms in page; every beat bottom lands above the footer at 390x664 and at 375x330 except beats taller than the space above the footer (an inherent limit, the top stays visible); every exercise and the end screen mount at scrollY 0; the swoon aside appears on the card only |

Not done: audio (tech debt 14) and the RLS cleanup (tech debt 2), both outside scope by the owner's decision.

## Phase 4: Review

- Commits on main, in order: c560dde CORS (D36), a41a3cf scroll fix, 66a2a6d orders helper, 06c72bd lesson 7 and the Unit 3 horizon, then the docs close-out. No push unless asked.
- Docs: this plan; DECISIONS.md D36; docs/tech-debt.md rows 24 and 25 removed, rows 26 (feedback sheet animation) and 27 (long banks, tall sheets, safe area) added from the scroll reader's findings; docs/architecture.md session flow; docs/rollback.md CORS notes; docs/deploy.md and both READMEs (in the CORS commit).
- Feature flag: none. CORS defaults to the local origins; the scroll change has no behavioral switch.
- Knowledge share: `rizalai orders <lesson.yaml>` before review, with --phrases and --bank when a marker phrase or a bank particle could move; the reviewer's chapter corpus file with a trap list stays the first brief for every new chapter; draft new lesson files in the scratchpad and copy in when green.

## Phase 5: Retrospective

What worked:
- Small, independent tasks with one reviewer each surfaced two bugs that tests written by the author could not see (the effect-order cancellation, the intersected flags). The independent red runs and the production-build probe were the difference.
- Asking the owner the six decisions up front with the facts from exploration; no task waited on a question mid-flight except the stub guard, which nobody had foreseen.
- The play-through of plan 005 paid for itself twice: both of this plan's fixes came from it.

What did not:
- The content test's "at least one stub" guard blocked the builder at the last step. Tests that encode a passing state of the content tree should say so in the plan's behaviors so the plan can change them on purpose.
- The reader's design for the helper was taken at face value; the reviewer found that its flags did not compose. Designs that promise coverage need a superset test in the brief, not after.
- One staged deletion rode into the wrong commit and had to be rewritten before push. Stage per commit from a clean index.

Change for plan 007:
- Decide the audio path (tech debt 14) or the deployment (Railway provisioning) next; eight lessons now ship on fakes and every finding of the last two plans came from playing real content.
- Use the orders helper in the reviewer's first pass on every lesson and record any natural order it cannot reach in the plan.
- Pay tech debt 26 and 27 together with the first real-device play-through; the 330px run shows a beat taller than the viewport's free space keeps its top visible and its gloss under the footer, which item 27's scroll container would also fix.
- The gloss underline includes trailing punctuation in the tappable token (cosmetic, pre-existing); fold into the next runner touch.
