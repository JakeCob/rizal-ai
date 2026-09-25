# Plan 005: Accepted word orders, unit flag cleanup, San Diego lessons 5 and 6

Workflow phases 0 to 5. Status: complete. Date: 2026-09-25. Run by an architect session with two Herdr workers (builder, reviewer); the architect runs the suites as tester because the Cursor tester is out of usage.

Scope, grilled with the owner on 2026-09-25: pay tech debt 17 (a token grader that accepts alternate natural word orders) and 18 (case-folded tile matching), re-author the exercises that plan 004 bent around exact match, drop the inert Unit.published flag (tech debt 19) and fix the done-but-unpublished tree node (tech debt 22), then author Unit 2's first two lessons from Noli chapters 10 (The town) and 13 (Signs of storm). No audio, no deployment, no RLS cleanup in this plan (see Phase 1).

## Phase 0: Setup

### Analysis

Grading today. Both graders compare a tapped token list with `answer_tokens` by strict equality: `grade_response` in apps/api/src/rizalai/progress/rules.py and `grade` in apps/web/lib/runner/grade.ts. No case folding, no alternate orders. The bank is authored in YAML and rendered in authored order; tiles are tracked by bank index and emit their authored string, so a capitalized first tile pins the sentence start. Plan 004 found ten exercises whose tiles admitted a second natural order and bent each one (plan 004 says nine; the review reports list ten). Three of them no longer match the beat they follow. `grade_response` has no unit test at all.

What accepted orders touch, verified by reading code: the three token models in contracts/lesson.py (extra=forbid, so YAML cannot carry a field the model lacks), `ANSWER_FIELDS` in content/seed.py (decides answer column versus payload), `grade_response`, the web `grade`, packages/contracts/schema.json and apps/web/lib/types.generated.ts (both CI drift gates), and apps/web/lib/api/fixtures.ts (the export marks every property required, so the mock lesson must gain the field or typecheck fails). No migration: exercises.answer is JSONB. The practice page posts to the server and the mock client calls the web grader, so both paths are covered by the two grader changes.

Content hash. `content_hash` hashes the full LessonContent dump, and pydantic emits defaulted fields, so adding `accepted_orders: []` moves every published lesson's version on the next seed. Decision: accept the one-time bump. There are zero learners, zero progress rows and zero cached reflections anywhere (dev database checked; Railway not provisioned), `user_progress.lesson_version` is written and never read, and the tree marks done from `completed_at`. Any future defaulted field will bump every version the same way; canonicalizing the hash is deferred until a learner exists.

Unit flag. `Unit.published` is seeded and never read: the tree, the published-lesson helpers and the review queue gate on `Lesson.published` only. Unit 2 renders byte-identically with the flag false. The owner's horizon (a visible unit with locked lessons) is delivered by lesson flags. Decision D35: drop the field. Tech debt 22 (a done lesson that is later unpublished stays a tappable done node that 404s) is a two-line change in `get_tree`: done only if still published, else locked.

Corpus. Chapters 10 and 13 carry the same chapter number in all three editions. Chapter 10: es 7 paragraphs, tl 7 body paragraphs (rows 8 to 14 are a footnote header and footnotes tagged body; never pin past tl 10:7), en 6 (Derbyshire merges es 4 and 5 into en 4, and en 5 covers es 6 plus the first half of es 7). Chapter 13: es 57, tl 57 body (58 is an illustration caption, 59 a footnote header; never pin past tl 13:57), en 39 (en 2 merges es 3 to 5; en 16 merges es 22 and 23; en 29 merges es 39 and 40). Chapter 10 has no dialogue except the boys' cry. Crispin and the sacristans are chapter 15, not 13.

Sensitivity. Pinned passages show on the card verbatim with no filter, so the only control is which paragraphs are pinned. Owner's rule: pin the paragraph that carries the plot point, not the slur. Chapter 13's lake paragraph (es/tl 13:38, en 13:28) carries the grave-digger's comparison about the Chinese cemetery and is not pinned; es/tl 13:35 and en 13:26 carry the exhumation and are pinned instead. Chapter 10's hanging is stated plainly in one beat. Chapter 10's first paragraph (Chinese merchants) is pinned for the town group; the vignette line stops at the crops.

D01 for short lines. Chapter 13's dialogue has short lines whose natural modern rendering coincides with Poblete's sentence modernized (tl 13:23, 13:31, 13:49). Owner's rule: no exemption; every such line gets a different natural wording, and the reviewer receives the chapter's tl rows in the first brief.

Scenes chosen by the owner. Lesson 5, chapter 10, the legend of the balete wood, narrator-led: seven narrated beats (speaker null, the lesson 3 precedent) and the boys' cry as the eighth. Lesson 6, chapter 13, the grave-digger interrogation: Ibarra, the old servant and the grave-digger at the cemetery, eight groups with the question-and-answer rhythm.

### Behaviors

Grading (both graders, one shared case table):
- Given a token exercise with `accepted_orders`, when the learner taps a sequence equal to `answer_tokens` or to any listed order, then the answer is correct on the client, on POST /attempts, on completion re-grading and on POST /review/answer.
- Given the same exercise, when the learner taps an order not listed, a prefix, or a superset, then the answer is wrong and a heart is spent as before.
- Given any of the three token types, when the tapped tokens differ from a correct sequence only by letter case, then the answer is correct.
- Given an exercise row seeded before this change (no `accepted_orders` key in the answer column), when it is graded, then it grades on `answer_tokens` alone.
- Given a comprehension_mc exercise, when graded, then behavior is unchanged.
- Given a wrong answer, when the feedback sheet shows the correct answer, then it shows `answer_tokens` (the canonical order), not an alternate.

Contract and content:
- Given a token exercise in YAML with `accepted_orders`, when it is validated, then each order is non-empty, differs from `answer_tokens` and from the other orders, and is covered by the bank as a multiset; otherwise validation fails with the offending order named.
- Given a token exercise without the key, when validated, then it validates and dumps `accepted_orders: []`.
- Given the seed, when an exercise carries `accepted_orders`, then the key lands in the answer column, not the payload, and GET /lessons/{id} ships it to the client with `answer_tokens`.
- Given the exported schema, when compared with the committed packages/contracts/schema.json and apps/web/lib/types.generated.ts, then there is no drift.
- Given real content, when the content tests run, then every accepted order's tokens carry no whitespace, and no listen_tap bank holds two tiles equal under lower() unless the transcript uses both.

Unit flag and tree:
- Given a unit.yaml with a `published` key, when loaded, then validation fails (UnitFile is extra=forbid).
- Given the migration, when upgraded, then units has no published column; when downgraded, then the column returns as NOT NULL default true.
- Given a lesson the learner completed, when it is later unpublished, then GET /tree shows it as locked (not done, not active) and GET /lessons/{id} is 404; the user_progress row and total_xp are untouched.

Re-authored exercises (lessons 1 to 4):
- Given each re-authored exercise, when seeded, then its key and uuid5 id are unchanged (renaming a key cascades attempts and review rows).
- Given each restored sentence, when the reviewer checks it, then the primary order matches the beat it follows and every listed alternate is natural spoken Tagalog.

Lessons 5 and 6:
- Given lesson 5 (noli-the-town) and lesson 6 (noli-signs-of-storm), when the content tests run, then each has 6 to 8 beats, 6 to 12 exercises, refs in aligned groups spanning at least two editions each with all three editions per lesson, unique locators, and no unpublished stub content.
- Given every vignette line, when compared with the chapter's tl rows, then none is Poblete's sentence with modernized spelling, including lines of five words or fewer.
- Given the pinned refs, when the card renders, then es/tl 13:38 and en 13:28 never appear, and no tl row past 10:7 or 13:57 is pinned.
- Given the seed on the dev database, when it runs, then 0 unresolved refs and lessons 5 and 6 replace the two stubs; the chapter 23 stub stays locked.

### Phases of work and parallelism

- A. Grader, both sides (builder): contracts, seed split, `grade_response`, web `grade`, export and regenerate, fixtures, shared case table, tests red first on each side. Reviewer reviews with independent red runs.
- B. Unit flag drop and tree fix (builder, after A's review, because A and B both touch content/seed.py and the content tests): loader, seed, model, migration, `get_tree`, content and fixture unit.yaml, tests red first.
- C. Re-author lessons 1 to 4 exercises with accepted orders (builder, after A lands in the working tree). Reviewer reviews Tagalog and orders; owner reads the changed lines.
- D. Lesson 5, The town (builder, can be authored while A is in review; validates once A is in the tree). Reviewer audits against tl 10:1 to 7.
- E. Lesson 6, Signs of storm (builder, after D). Reviewer audits against tl 13:1 to 57.
- F. Architect after each handoff: suites, seed, em dash grep, one play-through per new lesson at 375px against the dev database; docs, tech debt, decisions, commits.

Dependencies: B after A review. C after A. E after D. Commits in order: A, B, C, D+E, with docs in the last.

### File ownership

| Worker | Files |
|---|---|
| builder (A) | apps/api/src/rizalai/contracts/lesson.py, content/seed.py (ANSWER_FIELDS only), progress/rules.py, tests/unit/test_contracts.py, tests/unit/test_grade.py (new), tests/unit/test_content_loader.py, tests/integration/test_seed_and_lessons.py, test_progress.py, test_review.py, tests/fixtures/lesson_example.py, tests/fixtures/content/**, packages/contracts/schema.json, packages/contracts/grading-cases.json (new), apps/web/lib/runner/grade.ts, grade.test.ts, apps/web/lib/api/fixtures.ts, apps/web/lib/types.generated.ts |
| builder (B) | apps/api/src/rizalai/content/loader.py, content/seed.py, db/models.py, alembic/versions/<new>_drop_unit_published.py, lessons/router.py, tests/integration/test_published_only.py, content/units/*/unit.yaml, tests/fixtures/content/units/01-test-unit/unit.yaml |
| builder (C, D, E) | content/units/01-noli-arrival/*.yaml (C), content/units/02-san-diego/01-the-town.yaml and 02-signs-of-storm.yaml (D, E), content/units/02-san-diego/unit.yaml (D) |
| reviewer | reads everything, writes reports to the architect's scratchpad, edits nothing |
| architect | docs/plans/005-grader-and-san-diego.md, DECISIONS.md, docs/tech-debt.md, docs/architecture.md, docs/rollback.md, docs/plans/004-unit-one.md (count fix), apps/api/src/rizalai/progress/router.py (AttemptIn.correct description) |

### Authoring norms carried from plan 004, amended here

- target_vocab holds 15 to 20 entries keyed on the exact form used in a line; the root goes in note.
- Every token exercise has one primary order in `answer_tokens` that matches the beat it follows. Every other natural spoken order that the bank can build is listed in `accepted_orders`. Distractors may not complete an unlisted natural sentence.
- Tiles are compared case-insensitively, so a bank may hold Galit and galit when the transcript needs both. Authors still avoid repeated words in listen_tap transcripts unless the repetition is the teaching point.
- A vignette line that is Poblete's 1909 sentence with modernized spelling is a D01 violation, whatever its length. The reviewer compares every line against the chapter's tl rows, supplied in the brief.
- Pin the paragraph that carries the plot point, not the slur. Never pin tl rows that are captions or footnote headers.
- Speaker labels: Ibarra, Matandang alila, Tagapaglibing, Mga bata; narrator beats keep speaker null. Same character, same label across lessons.
- Sentence-case titles matching the chapter title: "The town", "Signs of storm". Slugs noli-the-town, noli-signs-of-storm. Exercise keys ex1 to exN never change once merged.

## Phase 1: Document

Tech debt: this plan closes 17, 18, 19 and 22 (rows removed at merge). It also removes rows 3 and 5, which plan 002 paid and nobody removed (row 6, no audio, is still true). New: 23, the content hash includes defaulted fields, so any new optional field re-versions every lesson once; canonicalize when a learner exists. Tech debt 2 (RLS cleanup, task E of plan 004) and 14 (TTS bake-off) stay open; lessons 5 and 6 ship with null audio_url like lessons 1 to 4, so SPEC non-negotiable 5 stays unmet until the owner picks an engine by ear.

Rollback: revert the commits in reverse order. The grader commit reverts cleanly (re-export the schema and regenerate types as part of the revert, or CI drifts). The unit flag commit's migration has a downgrade that restores the column with server default true. Content commits re-seed on revert; lessons 5 and 6 fall back to the stubs. Progress rows survive every case. docs/rollback.md gains a line on contract reverts and loses the Supabase wording.

## Phase 2: TDD plan

Red first on each side, output shown in the report. Shared case table: packages/contracts/grading-cases.json, a list of {type, answer_tokens, accepted_orders, tokens, correct} read by tests/unit/test_grade.py (pytest) and lib/runner/grade.test.ts (Vitest), so the two graders cannot drift silently.

API, task A:
1. tests/unit/test_contracts.py: order not covered by bank rejected; empty order rejected; order equal to answer_tokens rejected; duplicate orders rejected; missing key validates as []; schema export has `accepted_orders` on SentenceAssembly, TranslateLine and ListenTap.
2. tests/unit/test_grade.py (new): every row of grading-cases.json; missing key grades on answer_tokens; non-list tokens wrong; comprehension_mc unchanged.
3. tests/integration/test_seed_and_lessons.py: `accepted_orders` in answer column, absent from payload, present in GET /lessons/{id}.
4. tests/integration/test_progress.py and test_review.py: an alternate order posts correct with hearts unchanged; completion re-grades it correct; /review/answer accepts it.
5. tests/unit/test_content_loader.py: whitespace check over accepted orders; listen_tap banks have no case-only duplicates unless the transcript uses both.
6. Green: contracts field and validator, ANSWER_FIELDS, grade_response with lower() over tokens and every candidate, export, gen:types, fixtures.

Web, task A:
7. lib/runner/grade.test.ts: the same case table; unlisted reorder still false; correctAnswerText still joins answer_tokens.
8. Green: grade.ts compares response.tokens against answer_tokens and each accepted order with toLowerCase(); fixtures gain `accepted_orders`; pnpm typecheck, lint, test green; e2e untouched (MOCK_LESSON's first exercise unchanged so the 200ms check keeps its baseline).

API, task B:
9. tests/unit/test_content_loader.py or test_published_only.py: UnitFile rejects a `published` key (red today).
10. tests/integration/test_published_only.py: tree locks a done lesson once unpublished, GET 404, progress row intact (red today: done).
11. Green: remove the field from loader, seed, model; migration drop column with downgrade; get_tree done-only-if-published; unit.yaml files lose the key. Architect runs `alembic downgrade -1` then `upgrade head` on rizalai_test.

Content, tasks C, D, E: the content tests are the red bar; a lesson file that fails them is not handed to review.

### Checklist

- [x] A. Grader with accepted orders and case folding on both sides, shared case table, export and types regenerated, tests red first: builder, reviewer
- [x] B. Unit.published dropped with migration, tree locks done-but-unpublished lessons: builder, reviewer
- [x] C. Lessons 1 to 4 re-authored: L2 ex6 (pa restored), L2 ex3 (trailing kay), L2 ex4 (Galit na galit transcript back), L3 ex2 (ba back), L3 ex6 (Dahil doon restored), L4 ex3 (kaya back, owner judges), L4 ex8 (Sige restored), L1 ex7 (ay-less order accepted); English-side cases left as they are; keys unchanged: builder, reviewer, owner read
- [x] D. Lesson 5, The town (noli-the-town, chapter 10, balete legend, narrator-led, groups town, wood, legend, family, boys): builder, reviewer, owner read
- [x] E. Lesson 6, Signs of storm (noli-signs-of-storm, chapter 13, grave-digger, groups arrive, cross, missing, ask, burned, dug, lake, wretch; lake pins 13:35 and en 13:26): builder, reviewer, owner read
- [x] F. Architect: suites and seed after each handoff, migration down and up, one play-through per new lesson at 375px, docs (D34, D35, tech debt, architecture, rollback, plan 004 count), AttemptIn.correct description fix with re-export, commits on main, no push unless asked

## Phase 3 record

Run as an architect session with two Herdr workers: builder (Claude) wrote every code and content change, reviewer (Claude) reviewed every change with independent red runs against HEAD copies and a line-by-line D01 audit against the chapter's Poblete rows, and the architect ran the suites, the seed and the migration cycle after each handoff and played the new lessons at 375px through an in-process tester agent (the Cursor tester stayed out of usage). Exploration before grilling ran as an in-process workflow: six readers over the grader, the web runner, the reshaped content, the unit flag, the chapter 10 and 13 corpus, and the plan conventions, plus a critic that filled gaps and drafted the owner questions; nine of its thirteen questions were settled by code or a default and six went to the owner.

Review findings by task:
- A, grader: MERGE on first review with four should-fixes (case-insensitive distinctness in the validator, empty stored orders, the web grader throwing on malformed data, punctuation in the case-only duplicate test) and three nits (bool as an index, a shared TokenExercise base, one coverage helper), all folded in as A2 and re-checked MERGE. Every new test was shown red against a HEAD copy, and a flipped case-table row failed both suites.
- B, unit flag: MERGE with two should-fixes (a stale line in docs/architecture.md, a tree test that could not see the next active lesson), both applied. The test database was stamped at the new head during the seconds between `alembic revision` writing its stub and the builder filling it in; repaired with stamp and upgrade on rizalai_test only, and recorded here so nobody is surprised by it.
- C, lessons 1 to 4 re-authored: FIX for two lesson 1 exercises whose banks built natural orders nobody had listed (three orders added), then MERGE. Keys unchanged, so ids, attempts and review rows survive.
- D, lesson 5: FIX for one distractor that completed an unlisted natural English order and two lines that read as translated English (the town selling its crops, an object verb for a hanged man), then MERGE. The builder caught that the brief's own boys' cry was a Poblete line and rewrote it.
- E, lesson 6: FIX for one unlisted natural order and one missing particle order, plus wording nits (spoken no'n, trampling rather than passing over the graves, symmetric cards where Derbyshire merges), then MERGE. On the hardest D01 chapter so far, no beat matched a trap line with or without pronouns, after the builder rewrote eight near misses during drafting.

Owner gate on 2026-09-25: lessons 5 and 6 read and approved (English kept on the lake card); the kaya order and the ay-less orders accepted as correct.

Results at the end of the plan:

| Suite | Result |
|---|---|
| API pytest | 185 passed, 87.0 percent coverage, ruff and mypy strict clean |
| Web Vitest | 67 passed (14 shared grading cases plus malformed-data mirrors), lint and typecheck clean |
| Playwright e2e | 3 passed on the iPhone project, mock mode |
| Migration | 40506cb22e4f cycled up, down and up on the dev database; downgrade restores the column NOT NULL default true |
| Seed on the dev database | 2 units, 7 lessons, 60 exercises, 0 unresolved refs (lesson 5: 17 refs in 5 groups; lesson 6: 31 refs in 8 groups) |
| Play-throughs at 375px | Lessons 5 and 6 played end to end in headless Chromium (iPhone 13 device) against the real API and the dev database after completing lessons 1 to 4 through the API: 20 exercises, 7 answered with a listed alternate (all correct on the client and on the server re-grade), 2 deliberate wrong answers (sheet shows answer_tokens, one heart each), 90 XP per lesson, 0 console errors, 0 failed requests, no horizontal overflow, focus rings visible, every audio control present and disabled. Check to result max 13 ms, median 7 ms; Continue to next screen max 33 ms, median 17 ms (in-page). The excluded lake paragraph appears on no card. Two findings outside this plan's scope are logged as tech debt 24 and 25 |

Not done: the RLS cleanup (tech debt 2) and audio (tech debt 14), both outside this plan's scope by the owner's decision.

Found by the play-through, not fixed here (both predate this plan):
- The API has no CORS middleware, so a browser on another origin cannot call it at all (every request preflights because of Authorization, Content-Type and X-Timezone, and OPTIONS returns 405). The tester had to launch Chromium with web security disabled to play at all. Web on Vercel and API on Railway are different origins, so this blocks the first deploy. Tech debt 24.
- From the third beat on, the newly revealed vignette line sits below the fixed footer and nothing scrolls it into view; the learner must scroll by hand after every Continue. Tech debt 25.

## Phase 4: Review

- Commits on main, in order: 3a75410 grader (D34), 6ba34ac lessons 5 and 6, 662a5e9 unit flag and tree fix (D35), c856e71 Unit 1 exercises re-authored, then the docs close-out. No push unless asked.
- Docs: this plan; DECISIONS.md D34 and D35; docs/tech-debt.md rows 17, 18, 19 and 22 removed, rows 3 and 5 removed as already paid, row 23 added; docs/architecture.md units and answer column lines; docs/rollback.md contract-revert note and the Supabase wording; docs/plans/004-unit-one.md count corrected to ten; AttemptIn.correct's description now says the flag is ignored (re-exported).
- Feature flag: none. accepted_orders defaults to empty, so lessons without it behave as before; case folding changes no outcome for current content.
- Knowledge share: the amended authoring norms above are the checklist for Unit 2's remaining lessons. The shared case table in packages/contracts/grading-cases.json is where a new grading rule goes first; both suites read it. The reviewer's corpus files with Poblete trap lists (in the architect's scratchpad for this session) are the pattern for every future chapter brief.

## Phase 5: Retrospective

What worked:
- Paying the grader debt before authoring: lessons 5 and 6 carry natural primaries and listed alternates with no workarounds, and the re-authoring restored three exercises to the beats they follow.
- Exploration before grilling. The critic caught that the sensitivity question as first phrased was about chapter 15, not 13, and that a defaulted field bumps every content hash, so the owner decided both with the facts in hand.
- The Poblete trap list in the reviewer's first brief. The D01 check happened while drafting; both lessons were clean on first review, which plan 004's retro asked for.
- Drafting a new lesson file in the scratchpad and copying it in only when green kept the reviewer's concurrent full-suite runs stable.
- Committing the grader as soon as it was verified freed the shared files for Task B without hunk splitting.

What did not:
- Reviews still found unlisted natural orders in three lessons on first pass (D ex4, E ex2 and ex7, C ex6 and ex7). Enumerating every order a bank builds is mechanical; a script that lists them for the reviewer would make the judgment call the only work.
- The `alembic revision` stub race against a concurrent test run stamped the test database early. Write the migration body before saving, or run the suite only after the file is complete.
- The brief for lesson 5 quoted a Poblete line as the boys' cry. Briefs that quote source text should be checked against the trap list too.
- The ratio of review rounds to tasks is still about two to one. That is the cost of the Tagalog gate and it is worth paying, but plan sizing should assume it.

Change for plan 006:
- Fix tech debt 24 (CORS) and 25 (scroll the current beat into view) first; both are small and both block a phone play-through by a real learner.
- Add a content test or authoring script that enumerates buildable token orders per exercise for the reviewer.
- Decide the audio path (tech debt 14) before authoring more lessons; six lessons now ship with disabled play buttons.
- Carry the RLS cleanup (tech debt 2) into the first plan with a working tester.
- Canonicalize the content hash (tech debt 23) before the Railway database exists.
