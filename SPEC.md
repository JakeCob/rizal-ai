# RizalAI Product Specification

Version 1.0, 2026-09-17. Owner-approved architecture in docs/architecture.md. Decisions in DECISIONS.md.

## 1. Purpose

RizalAI teaches Tagalog and Rizal's literature at the same time. Learners work through a skill tree of short lessons. Each lesson is a narrative vignette from Rizal's world, broken into tap-through exercises, and ends with the original passage the vignette was drawn from plus a reflection in Rizal's voice grounded in his writings.

The product is Duolingo Stories with Rizal as the story spine. Production quality, not a demo.

## 2. Audience

- Heritage learners and foreigners who want Tagalog through a substantive cultural spine.
- Filipino students who did Rizal in high school but never engaged with the text.

Design bias: assume the learner knows nothing. Scaffold everything, including 19th-century vocabulary a Filipino student may not know.

## 3. Non-negotiables

1. No hallucinated Rizal. Any span presented as Rizal's own words traces to a retrieved passage or the authored spine, verified by code.
2. Tagalog quality. Generated Tagalog that reads as translated English fails. The LLM is prompted with real Rizal-era passages as style context.
3. Mobile-first. If it does not feel right at 375px wide, it is not done.
4. Latency. Exercise transitions under 200ms perceived. Generated content is prefetched or streamed behind a skeleton.
5. Accessibility. Keyboard-navigable, screen-reader labels on every tap target, audio for every vignette line.
6. No em dashes in user-facing copy or comments.

## 4. MVP scope

In scope:
- Skill tree of units. Each unit 3 to 6 lessons. Each lesson 3 to 7 minutes.
- Lesson structure: 4 to 8 line vignette, then 6 to 12 exercises across four types: sentence_assembly, translate_line, listen_tap, comprehension_mc.
- XP per exercise, daily streak, hearts, spaced repetition review queue.
- "In Rizal's voice" card: original passage in Spanish, 1909 Tagalog, and English, plus a bilingual generated reflection with cited quotes.
- Anonymous auth with persistent progress.
- Corpus: Noli Me Tangere in three languages.

Out of scope for MVP: voice input and output, Ilokano, social features, multiplayer, fine-tuning, word_picture exercises, offline lessons, streak freezes, account linking UI, personalized reflections.

Architected for later without rewrite: voice (TTSClient and a future STTClient protocol), Ilokano (language column on every content row), the other three works (work and translator columns), word_picture (discriminated union).

## 5. First deliverable

One playable lesson: Noli Me Tangere, Chapter 1, Ibarra's introduction at Capitan Tiago's dinner.

Definition of done, each item executable as a test:
- Skill tree shows this lesson unlocked and at least three placeholder locked lessons after it.
- The lesson has 6 to 10 exercises across the four types, with audio on every vignette line.
- The "In Rizal's voice" card is populated by the reflection pipeline from real Chapter 1 text, citations validated.
- XP is awarded, the streak increments, and progress persists across a page reload.
- The whole flow passes a Playwright run in an iPhone viewport.

Build order, fixed by the owner: architecture doc, then scaffold (API health and mock lesson endpoint, web tree and runner shell, Noli ingest), then author the Chapter 1 lesson and wire the reflection endpoint. No LLM integration before the plumbing is solid.

## 6. Behaviors

Written as Given, When, Then. These are the acceptance criteria for the first deliverable and the source for test names.

### 6.1 Identity and progress

- Given a first-time visitor, when they open the app, then an anonymous session is created and the skill tree renders without a sign-up form.
- Given a learner with progress, when they reload the page, then XP, streak, hearts, and lesson completion are unchanged.

### 6.2 Skill tree

- Given the seeded content, when the tree loads, then the Chapter 1 lesson node is active and later nodes are locked.
- Given a locked node, when tapped, then a popover explains it is locked and no lesson starts.
- Given the active node, when tapped, then a popover shows the lesson title, estimated minutes, and a Start button with the XP reward.
- Given a completed lesson, when the tree loads, then its node shows as done and the next node is active.

### 6.3 Lesson runner

- Given a lesson is opened, when the runner mounts, then the whole lesson including audio URLs is fetched once and the reflection request is fired in parallel.
- Given a vignette, when the learner taps continue, then the next line reveals, its audio plays, and previous lines dim.
- Given a vignette line, when the learner taps a Tagalog word, then a bottom sheet shows its English gloss and plays the word audio.
- Given an exercise, when the learner submits a correct answer, then a green feedback sheet appears, XP for the exercise is shown, and Continue advances within 200ms of tap.
- Given an exercise, when the learner submits a wrong answer, then a red feedback sheet shows the correct answer and one heart is removed.
- Given a wrong answer, when the attempt is posted, then the UI does not wait on the response.
- Given zero hearts, when the next wrong answer happens, then the runner exits to the practice-to-refill screen.
- Given the last exercise is completed, when the completion request succeeds, then the "In Rizal's voice" card shows with the cached reflection already present.

### 6.4 In Rizal's voice card

- Given a completed lesson, when the card renders, then the Spanish, 1909 Tagalog, and English passage layers are shown, each labeled, each collapsible.
- Given the reflection, when the learner toggles language, then the Tagalog and English versions swap without a network call.
- Given a quoted span in the reflection, when rendered, then it is visually distinct, and it is a verbatim substring of the cited passage.
- Given a reflection that failed validation twice, when the card renders, then only the passage layers show and no generated text appears.

### 6.5 Completion, XP, streak, hearts

- Given attempts for a lesson, when completion is posted, then the server re-grades them and total_xp increases by the sum of correct exercise XP.
- Given last_activity_date is yesterday in the learner's timezone, when a lesson completes, then streak_count increments by one.
- Given last_activity_date is today, when a second lesson completes, then streak_count is unchanged.
- Given last_activity_date is two or more days ago, when a lesson completes, then streak_count resets to one.
- Given hearts were spent 4 hours ago, when the user is read, then one heart has regenerated.

### 6.6 Review queue

- Given a completed lesson, when completion is posted, then each exercise has a review_queue row with an FSRS state and due_at.
- Given a practice-to-refill session, when 10 due items are answered, then hearts refill to 5.

### 6.7 Reflection pipeline

- Given a lesson with pinned passages, when the reflection is requested and no cache row exists, then one structured LLM call is made and the result is validated and cached.
- Given a cache row exists, when the reflection is requested, then no LLM call is made.
- Given a generated quoted span that is not a verbatim substring of its cited passage, when validated, then the row is regenerated once, and on second failure marked fallback.
- Given a rejected cache row, when the reflection is requested, then a new generation runs.

### 6.8 Corpus ingest

- Given the Noli source files, when ingest runs, then every paragraph becomes a source_passages row with work, language, translator, chapter, paragraph_index, char offsets, and license_note.
- Given ingest runs twice, when the second run completes, then no duplicate rows exist.
- Given a passage row, when embedded, then dense and sparse vectors and the model name are stored.

## 7. Data model

See docs/architecture.md section 3. Tables: users, units, lessons, exercises, source_passages, exercise_attempts, user_progress, review_queue, generated_content_cache.

## 8. Interfaces

- GET /health
- GET /tree
- GET /lessons/{id}
- GET /lessons/{id}/reflection
- POST /attempts
- POST /lessons/{id}/complete
- GET /review/due
- POST /review/answer
- GET /me

All endpoints except /health require a Supabase JWT.

## 9. Non-functional requirements

- Exercise transition under 200ms perceived, measured in the Playwright run.
- Lesson fetch under 1s on a simulated 4G connection.
- Reflection served from cache under 300ms; cold generation is off the critical path.
- 80 percent test coverage on API and web.
- Every tap target at least 44px and labeled for screen readers.
- Works at 375px wide with no horizontal scroll.

## 10. Open items

- Licensing check for Fili and the essay and letter translations before any ingest beyond Noli.
- TTS engine, pending the bake-off.
- LLM provider, pending the blind eval.
- Judge score threshold, after the first 10 generations are hand-reviewed.
- Design direction (D28) awaiting owner approval; scaffold uses it as the working default.
