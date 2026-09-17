# Plan 002: Chapter 1 lesson, progress, and the Rizal's voice card

Workflow phases 0 to 5. Status: in progress. Date: 2026-09-17.

Scope, from the owner's brief item 4 and SPEC.md section 5: hand-author the Noli Chapter 1 lesson (Ibarra's arrival and introduction at Capitan Tiago's dinner), persist progress (attempts, completion, XP, streak, hearts, review queue), and wire the "In Rizal's voice" endpoint that grounds a generated reflection in retrieved passages. Audio rendering waits on the TTS bake-off, but the TTS protocol and bake-off script are in scope.

## Phase 0: Setup

### Analysis

Plan 001 proved the plumbing with a placeholder lesson. This plan replaces the placeholder with authored content and closes the loop that SPEC.md calls the first deliverable: XP awarded, streak incremented, progress persisted, and the card populated by the reflection pipeline from real Chapter 1 text.

The scene: Rizal ends Chapter 1 with two figures entering the sala and opens Chapter 2 with Capitan Tiago introducing "Don Crisóstomo Ibarra" to the guests, Padre Damaso's reaction, and Ibarra's greeting to the company. The lesson's pinned passages therefore span the end of Chapter 1 and the start of Chapter 2, hand-aligned across the three languages by content (chapter counts and paragraph splits differ per edition; docs/tech-debt.md item 10).

Content rule from D01: the drilled vignette is our own modern Tagalog, adapted from the scene. The card shows the originals verbatim. Nothing generated carries Rizal's byline except verbatim spans validated by code (D03).

No credentials exist locally. The reflection pipeline is built and tested against a FakeLLMClient that returns canned structured output; the Anthropic adapter is tested against recorded request and response shapes. The real call runs once the owner adds ANTHROPIC_API_KEY.

### Behaviors

From SPEC.md sections 6.3 to 6.7, restated for this plan:

Content:
- Given the Chapter 1 YAML, when validated, then it has 6 to 8 beats and 8 to 10 exercises across all four types, every beat has both tl and en, and every source passage ref resolves after ingest.
- Given target_vocab, when the runner shows a beat, then tapping a Tagalog word that is in target_vocab opens a gloss sheet.

Attempts and completion:
- Given a valid JWT, when POST /attempts is called with exercise_id, correct, response, duration_ms, then 202 and a row exists scoped to the user.
- Given an exercise_id from another lesson or a nonexistent one, then 404.
- Given attempts for every exercise in a lesson, when POST /lessons/{id}/complete is called, then the server re-grades each latest attempt, total_xp increases by the sum of xp for correctly graded exercises, user_progress is upserted with completed_at, and review_queue has one FSRS row per exercise.
- Given a completion for a lesson with no attempts, then 409.
- Given a client that claims correct on a wrong response, when completion re-grades, then that exercise earns no XP.

Streak and hearts:
- Given last_activity_date is yesterday in the user's timezone, when completing, then streak_count increments. Today: unchanged. Older: resets to 1. Never: becomes 1.
- Given a timezone header on first request, then users.timezone is stored.
- Given hearts spent 4 hours ago, when GET /me is called, then one heart has regenerated, capped at 5.
- Given a wrong attempt, when posted, then hearts decrease by one server-side, never below zero.

Review queue:
- Given GET /review/due, then up to 10 due review_queue items with their exercises are returned.
- Given POST /review/answer with correct or not, then FSRS reschedules the row, and after 10 answered items hearts refill to 5.

Reflection:
- Given a lesson with pinned passages and no cache row, when GET /lessons/{id}/reflection is called, then one LLM call is made with the pinned passages plus style-context passages, the result is validated, cached, and returned.
- Given a cache row, then no LLM call is made.
- Given a quoted span that is not a verbatim substring of its cited passage, then regenerate once; on second failure return a fallback payload with passages only and status fallback.
- Given the response, then it contains the three passage layers (es, tl, en with labels) and the reflection with tl, en, and quoted_spans carrying passage ids.
- Given the CLI reflections list and reflections reject <id>, then the row is marked rejected and the next request regenerates.

Card UI:
- Given completion succeeds, when the card renders, then three collapsible labeled layers show the passages, the reflection shows with a tl/en toggle that swaps without a network call, and quoted spans are visually distinct.
- Given a fallback payload, then only the passage layers show.

### Phases of work

1. Content: author content/units/01-noli-arrival/01-ibarra-arrival.yaml, retire the placeholder, seed.
2. Progress API: timezone capture, hearts regen on read, POST /attempts, POST /lessons/{id}/complete with re-grading, streak, FSRS seeding. Tree marks done.
3. Review API: GET /review/due, POST /review/answer, hearts refill.
4. Retrieval: pinned passages by id plus style-context passages by chapter proximity; hybrid search deferred (tech debt 8).
5. Reflection: LLMClient protocol, FakeLLMClient, AnthropicClient with structured output, prompt v1, validator, judge stub, cache, endpoint, CLI list and reject.
6. Web: attempts posting, completion call, /me refresh, gloss sheet, card with layers and toggle, out-of-hearts practice flow.
7. TTS: TTSClient protocol, adapters (MMS-TTS, XTTS, Google), bake-off script, render script. Real rendering waits on the owner's ear.
8. Docs, CI, retro.

### Dependencies

1 before 5 (pinned passages) and before 6 (real content in the runner). 2 before 3 and before 6. 4 before 5. 7 is independent.

## Phase 1: Document

Tech debt candidates: judge threshold unset until 10 generations are reviewed (D21); audio_url stays null until the bake-off; the practice-to-refill flow reuses lesson exercises only.

Rollback: alembic downgrade for the two new migrations (users.timezone already exists, so likely only indexes), content revert restores the placeholder, cache rows are keyed by prompt_version so a prompt rollback is a version bump.

## Phase 2: TDD plan

API tests: unit for streak arithmetic, hearts regen, FSRS scheduling wrapper, validator, prompt assembly; integration for every endpoint above against the real database. Web tests: card component, gloss sheet, runner posting attempts through a mocked client, completion flow. Playwright: extend the play-through to assert the card and the XP on the tree afterwards, in mock mode with a mocked reflection.

### Checklist

- [ ] 1.1 Chapter 1 lesson YAML with aligned passage refs
- [ ] 1.2 Placeholder retired, seed shows 0 unresolved
- [ ] 2.1 X-Timezone header captured on the user
- [ ] 2.2 Hearts regen on read
- [ ] 2.3 POST /attempts
- [ ] 2.4 POST /lessons/{id}/complete: re-grade, XP, streak, progress, FSRS seed
- [ ] 2.5 Tree marks done and advances active
- [ ] 3.1 GET /review/due
- [ ] 3.2 POST /review/answer with refill
- [ ] 4.1 Retrieval by pinned ids plus context
- [ ] 5.1 LLMClient protocol, fake, Anthropic adapter
- [ ] 5.2 Prompt v1, structured output schema
- [ ] 5.3 Citation validator
- [ ] 5.4 Cache and endpoint with regenerate-once and fallback
- [ ] 5.5 CLI reflections list and reject
- [ ] 6.1 Attempts and completion wired in the runner
- [ ] 6.2 Gloss sheet on tap
- [ ] 6.3 Card with three layers, toggle, quoted spans
- [ ] 6.4 Out-of-hearts practice flow
- [ ] 6.5 Playwright extended
- [ ] 7.1 TTSClient protocol and adapters
- [ ] 7.2 Bake-off and render scripts
- [ ] 8.1 Docs, tech debt, decisions, retro
