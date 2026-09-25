# Plan 004: Finish Unit 1 (lessons 2 to 4), locked Unit 2, RLS cleanup

Workflow phases 0 to 5. Status: in progress. Date: 2026-09-25. Run by an architect session with three Herdr workers (builder, reviewer, rizal-tester).

Scope, grilled with the owner on 2026-09-25: three authored lessons that finish Unit 1, a locked Unit 2 with three placeholder lessons so the path keeps a horizon, and a cleanup migration that removes the dead Row Level Security policies (D33). No deploys, no credentials.

## Phase 0: Setup

### Analysis

Lesson 1 (noli-ibarra-arrival) already spans the end of Chapter 1 and the introduction in Chapter 2, so the remaining scenes come from later chapters. Chosen with the owner:

| Lesson | Slug | Scene | Register and speakers |
|---|---|---|---|
| 2 | noli-the-dinner | Chapter 3, The Dinner: the tinola, Padre Damaso's insult, Ibarra leaves | food, politeness, restraint; Damaso, Tiago, Ibarra, narration |
| 3 | noli-heretic-filibuster | Chapter 4, Heretic and Filibuster: Teniente Guevara tells Ibarra how Don Rafael died | past narration, grief; Guevara, Ibarra |
| 4 | noli-azotea | Chapter 7, An Idyl on an Azotea: Ibarra and Maria Clara | affectionate register, a female speaker; Maria Clara, Ibarra, Tiya Isabel |

Chapter 5 is five paragraphs and Chapter 6 is exposition, so both were skipped. Chapter 8 was considered and set aside for a later unit.

Rules carried from D01, D03, D19: the vignette is our own modern Tagalog adaptation; the originals appear only on the card through pinned passages; refs that describe the same passage across editions share a group so alignment is by content. English paragraph numbers differ from the Spanish and Tagalog within a chapter, so every ref is checked against the text, never inferred.

Unit 2 "San Diego" is a unit.yaml with three unpublished stubs and no content, mirroring how Unit 1's placeholders worked in plan 001.

Authoring norms settled during review (apply to every lesson from now on):
- target_vocab holds 15 to 20 entries, only words new to the unit or central to the beats. The tl value is the exact form used in a line (parehong, not pareho), because the gloss lookup matches the lowercased word; the root goes in note.
- Every token exercise must have one natural order. Distractors may not complete a second valid sentence. Until tech debt 17 lands, the reviewer flags any answer whose tiles admit another natural order.
- listen_tap transcripts avoid repeated words, so no two tiles differ only by case (tech debt 18).
- A vignette line that is Poblete's 1909 sentence with the spelling modernized is a D01 violation, even with a pronoun added. The reviewer compares every line against the chapter's tl rows.
- Speaker labels are consistent across lessons for the same character (Tenyente, Kapitan Tiago, Padre Damaso). Learner-facing English uses the Spanish spelling Teniente.
- Register follows the source: Kapitan Tiago addresses Ibarra with po and kayo; Padre Damaso and the lieutenant use mo, matching the Spanish tu and the lesson 1 precedent.
- Titles use sentence case after any colon ("The dinner", "Chapter 10: The town").
- Unit 2 stubs point at Chapter 10 (the town of San Diego), Chapter 13 (signs of storm, the cemetery), and Chapter 23 (fishing, Elias and the crocodile), the three scenes with the most dialogue before the fiesta.

Code findings from the lesson 4 review, fixed in this plan as Tasks G and G2. Behaviors:
- Given two units whose uuid order disagrees with their order_index, when GET /tree is called, then the active lesson is the first published lesson of the unit with the lowest order_index.
- Given an unpublished lesson, when GET /lessons/{id}, POST /lessons/{id}/complete, or GET /lessons/{id}/reflection is called, then 404, no progress row is written, and no LLM call is made.
- Given an exercise whose lesson is unpublished, when POST /attempts or POST /review/answer is called, then 404 and no attempt or review row is written; and GET /review/due never lists it.

RLS: migration 1a2b3c4d5e6f enables policies only when an auth schema exists. No database will ever have one now. A forward migration drops the policies and disables RLS where present, guarded the same way, and the original migration stays in history untouched.

### Behaviors

Content (each of the three lessons):
- Given the lesson YAML, when validated, then it has 6 to 8 beats, 8 to 10 exercises covering all four types, every beat has tl and en, every exercise_after points at a real key, and every source passage ref resolves after ingest with its group shared by two or three editions.
- Given the seed, when it runs, then Unit 1 has four published lessons in order, Unit 2 has three locked stubs, and the tree marks lesson 2 active once lesson 1 is done.
- Given the mock fixtures, then they are unchanged: the web tests keep the placeholder lesson as their fixture.
- Given the vignette lines, when the reviewer reads them, then none reads as translated English, spelling is modern orthography, and speakers match the scene. The owner reads the lines before merge.

Migration:
- Given a database that ran 1a2b3c4d5e6f, when the cleanup migration runs, then no policy named *_owner_select or *_read_all exists and RLS is disabled on the eight tables, on both a database with an auth schema and one without.
- Given downgrade, then the schema is unchanged (the policies are not recreated; the original migration remains the record of them).
- Given the test suite, then it passes with the new head.

### Phases of work and parallelism

- A. Lesson 2 (builder), B. Lesson 3 (builder, after A), C. Lesson 4 (builder, after B): sequential because one author keeps the voice consistent, and each lesson goes to review while the next is written.
- D. Unit 2 stubs (builder, with C, same files owner).
- E. RLS cleanup migration (rizal-tester authors, runs in parallel with A). Reviewer reviews E; builder runs the API suite against E as its tester.
- Review of A, B, C, D: reviewer (code-review plus review skills, Tagalog audit). Test of A, B, C, D: rizal-tester plays each lesson through the real API against the dev database with the run skill and Playwright at phone width.

### File ownership

| Worker | Files |
|---|---|
| builder | content/units/01-noli-arrival/*.yaml, content/units/02-san-diego/*.yaml |
| rizal-tester | apps/api/alembic/versions/<new>_drop_rls.py, apps/api/tests/integration/test_rls_cleanup.py |
| reviewer | none (reads only) |
| architect | docs/plans/004-unit-one.md, DECISIONS.md, docs/tech-debt.md, merges |

Each worker gets its own git worktree; the architect merges onto main. No pushes in this plan.

## Phase 1: Document

Tech debt: item 3 (placeholder lesson) is already closed. Item 2 (RLS no-op) was to close here but stays open, because E was parked (see the checklist). New: the three lessons carry fake audio until the bake-off, like lesson 1.

Rollback: revert the merge commits; the seed removes lessons dropped from unit.yaml, and the cleanup migration is forward-only by design.

## Phase 2: TDD plan

Content is tested by the existing content tests (test_real_content_directory_validates) plus a new assertion that every published lesson's refs resolve against the ingested corpus and that grouped refs cover at least two editions. The migration gets an integration test that applies head and asserts no policies remain. Playwright is unchanged (mock mode); the tester plays the real lessons manually through the run skill and reports.

### Checklist

- [x] A. Lesson 2, The Dinner: YAML, refs aligned (24 in 8 groups), seeded, reviewed twice, fixes applied; not played (tester blocked); owner read all eight lines and approved on 2026-09-25
- [x] B. Lesson 3, Heretic and Filibuster: same (25 refs in 8 groups); owner approved 2026-09-25
- [x] C. Lesson 4, An Idyl on an Azotea: same (25 refs in 8 groups); owner approved 2026-09-25
- [x] D. Unit 2 San Diego with three locked stubs: reviewed, MERGE
- [ ] E. RLS cleanup migration with test: parked by the owner on 2026-09-25 (the Cursor tester is out of usage and no substitute was used). Tech debt 2 stays open; carry E into the next plan that has a tester.
- [x] F. Content tests tightened: 11 tests, groups span editions per D19, locators and slugs unique across the tree, stubs empty, folder order matches order_index
- [x] G. Tree ordered by unit order; unpublished lessons return 404 on load, complete, and reflection (found by the lesson 4 review)
- [x] G2. Exercise-id endpoints and the review queue gated on published; helper moved to lessons/service.py
- [x] H. Merge as two commits on main (content and content tests; api gating, tests, and docs), no push; docs, tech debt 17 to 22, retro

## Phase 3 record

Run as an architect session with Herdr workers: builder (Claude) authored all content and code, reviewer (Claude) reviewed every change with the review and code-review skills plus a line-by-line Tagalog audit and an alignment audit against the corpus, and the architect ran the suites as the tester after each change. The Cursor tester ran out of usage before its first task, so the RLS cleanup (E) and the phone play-throughs did not happen; the owner was told and no substitute was used.

Each lesson went through two review rounds. Review findings by kind, across the three lessons: 5 lines that were Poblete's 1909 text with modernized spelling (D01), rewritten; 1 factual slip (a man who "fell" because he was stopped; the text has a push), fixed; 1 mistranslated joke (the chaperoning neighborhood), fixed; 10 token exercises whose tiles admitted a second natural order (the review reports list ten; an earlier draft of this record said nine), each fixed by changing the prompt, the answer, or a distractor (the root cause is logged as tech debt 17); 6 vocabulary entries that were never tappable because the line used a linked form, fixed by keying on the used form; register corrections (Kapitan Tiago now formal, Ibarra consistent with po). The reviewer also caught two of its own suggested wordings being too close to Poblete, and corrected them on re-check.

Results at the end of the plan:

| Suite | Result |
|---|---|
| API pytest | 139 passed, 86.8 percent coverage, ruff and mypy strict clean |
| Content tests | 11, mutation-checked by the reviewer (6 seeded faults, 6 caught) |
| Web Vitest | 47 passed, unchanged |
| Seed on the dev database | 2 units, 7 lessons, 40 exercises, 0 unresolved refs, 24 alignment groups |

Not done: play-throughs on the phone viewport (tester blocked) and the RLS migration (E), which the owner parked rather than reassign.

## Phase 4: Review

- Docs: this plan (norms, behaviors for G and G2), docs/tech-debt.md 17 to 22, DECISIONS.md unchanged (no new decision; D01 and D19 were applied, not changed). Rollback is the generic docs/rollback.md path: revert the two commits and re-seed.
- Feature flag: none. Unit 2 is visible but locked by content, not by a flag.
- Knowledge share: the authoring norms section above is the checklist for lesson 5 onward. The reviewer's reports in the architect's scratchpad are the worked examples.

## Phase 5: Retrospective

What worked:
- Separating author, reviewer, and tester caught what a single agent would have shipped: every lesson had at least one line of modernized Poblete on first draft, and the author had read D01. The reviewer's database comparison against the chapter's Tagalog rows is what found them.
- Reports written to files instead of read from panes. Pane scrollback lost the head of the first report; every later report was a file and nothing was lost.
- Verifying every handoff myself (content test, seed, em dash grep) before routing to review kept the reviewer on judgment calls rather than mechanics.

What did not:
- The exact-match grader shaped ten exercises. Authors had to avoid natural sentences because a second valid order would be marked wrong. Tech debt 17 (accepted orders) should be paid before lesson 5.
- The test brief was too loose on one rule and the reviewer had to relax it (D19's Tagalog-less passage). Rules that tests enforce should be quoted from the decision, not paraphrased.
- The Cursor worker was unusable from the start. Check every worker's usage state before assigning, not after.
- Blocking herdr waits settle on transient states; four waits returned early and had to be re-armed. Waiting on the report file's existence would be more reliable than waiting on agent state.

Change for plan 005:
- Pay tech debt 17 and 18 first, then author lessons 5 and 6 without the workarounds.
- Give the reviewer the Poblete rows for the chapter in the brief so the D01 check happens on first review rather than re-check.
- Decide Unit.published (tech debt 19) before Unit 2's first real lesson.
