# Decisions

Architecture decision log for RizalAI. One entry per decision, newest at the bottom. A decision is changed by adding a new entry that supersedes it, never by editing the old one. Status is one of proposed, accepted, superseded.

Format: context (what forced the choice), decision, consequences (what we now have to live with).

Grilling session: 2026-09-17. Architecture doc approved by the owner: 2026-09-17.

---

## D01. Learners drill modern Tagalog written by us, not the 1909 translation

Status: accepted, 2026-09-17

Context: the only public-domain Tagalog Noli is Pascual Poblete's 1909 translation, which uses pre-reform orthography ("manga", "nang") and period syntax. Learners drilling it would learn spellings that are wrong today.

Decision: authored vignettes and exercises are our own modern-Tagalog adaptation of each scene. Poblete's text appears only on the "In Rizal's voice" card, labeled as a 1909 translation, next to Rizal's Spanish and Derbyshire's English.

Consequences: the drilled text never carries Rizal's byline, so it is not bound by the no-hallucination rule. We never present modernized Poblete as Rizal's text. Any future normalized variant gets its own text_variant and its own label.

## D02. The reflection is bilingual, Tagalog first, one structured call

Status: accepted, 2026-09-17

Context: a lesson-one learner cannot read a Tagalog paragraph, but the product's identity is Tagalog. Two calls would double cost and let the versions drift. English-first would produce translated-English Tagalog, which the owner defined as a failure.

Decision: one structured LLM call returns {tl, en, quoted_spans}. The Tagalog is written first with retrieved Rizal-era passages as style context, then the English rendering. The card shows a toggle.

Consequences: prompt design must enforce Tagalog-first ordering. The judge scores the Tagalog, not the English.

## D03. A byline attaches to spans, and every span must be verbatim

Status: accepted, 2026-09-17

Context: the non-negotiable is no hallucinated Rizal, but the reflection is generated prose in Rizal's persona.

Decision: the card header reads "In Rizal's voice" with a visible note that the reflection is generated from cited passages. Inside it, only quoted spans carry the byline. A validator confirms each quoted span is a verbatim substring of its cited source_passages row before the row can be published.

Consequences: a failed validation regenerates once, then falls back to a passage-only card. The rule is enforced by code, not by the prompt.

## D04. Reflection is prefetched at lesson start and cached per lesson version

Status: accepted, 2026-09-17

Context: the card is the end-of-lesson reward. A skeleton at that moment breaks the experience. Personalized reflections would kill the cache.

Decision: the client requests the reflection when the lesson opens. Cache key is sha256 of (kind, lesson_id, lesson_version, prompt_version, model). Every learner sees the same reflection for a lesson version.

Consequences: reflections are reviewable and cost is a one-time event per lesson version. Personalization is a later feature with a separate cache scope.

## D05. Corpus MVP is Noli only, schema built for all four works

Status: accepted, 2026-09-17

Context: a public-domain Tagalog Fili is doubtful and the 20th-century Tagalog translations of the essays and letters are almost certainly still under copyright.

Decision: ingest Noli in Spanish, Poblete Tagalog, and Derbyshire English. source_passages carries work, language, translator, and license_note so the other works slot in later. A passage may exist with no Tagalog variant.

Consequences: licensing is checked per work before ingest, never after. The retriever must handle missing language variants.

## D06. Supabase Auth with anonymous sign-in from day one

Status: accepted, 2026-09-17

Context: progress must persist from the first lesson, and a sign-up wall before the first lesson kills conversion.

Decision: the first tap creates an anonymous auth.users row. Email or Google linking later keeps everything.

Consequences: users.id equals auth.users.id. Row Level Security works from day one. No homegrown device-ID scheme to migrate.

## D07. Authored spine lives as YAML in the repo, seeded to Postgres

Status: accepted, 2026-09-17

Context: content needs diff-based review and history like code, and progress rows need stable exercise IDs to point at.

Decision: one YAML file per lesson under content/, validated by Pydantic, seeded to units, lessons, and exercises tables. lesson_version is a content hash.

Consequences: the DB copy is what the API serves. Editing content is a PR. Exercise IDs are stable across seeds by being declared in the YAML.

## D08. Monorepo

Status: accepted, 2026-09-17

Context: one person, one product, two runtimes.

Decision: apps/api, apps/web, content/, packages/contracts, evals/, docs/. Pydantic models export JSON Schema; the web app generates TypeScript types from it.

Consequences: one PR per feature across both sides. Railway and Vercel each deploy a subfolder.

## D09. LLM default is Claude Opus 5 behind an interface, with an open-model eval harness

Status: accepted, 2026-09-17

Context: the owner wants open-source options explored, and Tagalog prose quality is non-negotiable. Open models lag on 19th-century register and have not been sampled.

Decision: claude-opus-5 via the Anthropic Python SDK is the default, behind an LLMClient protocol. evals/reflection holds 5 Noli passages and a rubric. A script runs Claude, SEA-LION v3, and Qwen 3 through a hosted provider; the owner grades blind. Provider is a config value.

Consequences: switching is an env var and a cache bust. The decision is made with samples in hand.

## D10. Embeddings are bge-m3, hosted, dense plus sparse

Status: accepted, 2026-09-17, supersedes the Voyage choice made earlier in the same session

Context: this is the layer where open source costs nothing to choose. bge-m3 has real Tagalog coverage and produces dense and sparse vectors in one pass, replacing a bolted-on full-text search hybrid.

Decision: bge-m3 through a hosted inference API. Dense vector in pgvector, sparse weights in jsonb, model name and dimension stored per row.

Consequences: re-indexing to another model is a script. The API process carries no model weights.

## D11. Web on Vercel, API on Railway, Postgres on Supabase

Status: accepted, 2026-09-17

Context: Supabase is required for Auth, RLS, and pgvector, so a Railway Postgres would be a second database. Vercel is the zero-config path for Next.js and gives PR preview URLs for phone review.

Decision: three vendors, each doing the one thing it is best at.

Consequences: three dashboards. Preview URLs per PR for reviewing a mobile UI.

## D12. TTS is pre-rendered at seed time, engine chosen by a bake-off

Status: accepted, 2026-09-17

Context: every vignette line needs audio, lines are known at seed time, and the 200ms transition budget cannot absorb a TTS call.

Decision: a seed script renders each line once into Supabase Storage keyed by content hash. A TTSClient protocol has adapters for MMS-TTS Tagalog, XTTS v2, and Google fil-PH. A bake-off script renders 3 lines with each; the owner picks by ear on a phone.

Consequences: no TTS in the request path. Re-rendering after the bake-off is cheap because of hash keying.

## D13. Exercise types at MVP: sentence_assembly, translate_line, listen_tap, comprehension_mc

Status: accepted, 2026-09-17

Context: word-picture matching needs an illustration per vocab item, a pipeline that does not exist.

Decision: four text and audio types. The exercise payload is a discriminated union on type.

Consequences: word_picture is a new variant later, not a schema change.

## D14. Thin client: the browser calls FastAPI, the whole lesson is fetched at start

Status: accepted, 2026-09-17

Context: the 200ms transition budget, the owner's depth in Python over Next.js, and the risk of business logic in two languages.

Decision: Next.js is a static shell. Client components use TanStack Query to call FastAPI with the Supabase JWT. The runner fetches the entire lesson once; every transition is local state. The browser never queries tables.

Consequences: Next.js server features go mostly unused. FastAPI is the only thing that touches Postgres.

## D15. Server-authoritative progress with per-attempt events and a transactional completion

Status: accepted, 2026-09-17

Context: XP must be trustworthy and a refresh mid-lesson must not lose everything, but every tap cannot wait on a round trip.

Decision: each answer POSTs an exercise_attempts row, fire and forget. Grading is local against the shipped answer key. Lesson completion is one transaction that re-grades attempts, awards XP, updates streak and hearts, upserts user_progress, and seeds review_queue.

Consequences: the client never persists a number it computed. The answer key ships to the client.

## D16. Hearts: 5, minus 1 per wrong answer, lazy regen 1 per 4 hours, zero ends the lesson

Status: accepted, 2026-09-17

Decision: regen is computed on read from hearts and hearts_updated_at. At zero the runner exits to a practice-to-refill screen that plays a review_queue session and refills to full.

Consequences: no cron. The practice flow reuses the SRS.

## D17. Streak extends on the first completion of the learner's local day

Status: accepted, 2026-09-17

Decision: users.timezone is captured from the browser on first session. The server computes the local date at completion. Increment if last_activity_date is yesterday, reset if older, no-op if today. Freezes and repair are out of scope.

Consequences: a Manila learner at 11pm keeps their streak.

## D18. Spaced repetition is FSRS

Status: accepted, 2026-09-17

Decision: py-fsrs with default parameters. review_queue rows carry stability, difficulty, last_review, reps, lapses, state.

Consequences: better retention modeling than SM-2 at the cost of a few more columns.

## D19. Passage alignment is one row per language paragraph with an optional group id, aligned manually where pinned

Status: accepted, 2026-09-17

Context: Poblete's paragraphs do not map 1:1 to Rizal's or Derbyshire's. Automated alignment errors would put the wrong Spanish under a Tagalog line on the byline card.

Decision: source_passages rows are (work, language, chapter, paragraph_index). passage_group_id links aligned rows. Only passages a lesson pins are hand-aligned at MVP.

Consequences: automated alignment is a later script that fills group ids, never a blocker.

## D20. Character tags are LLM-generated at ingest, marked by source, hand-corrected where pinned

Status: accepted, 2026-09-17

Decision: ingest tags each passage (characters, setting, speaker) against a fixed character list per work, stored in tags jsonb with tag_source. Pinned passages get reviewed and set to human.

Consequences: retrieval filters can use tags without trusting them for the byline.

## D21. Quality gate: citation validator (hard), judge score (threshold), one-command reject

Status: accepted, 2026-09-17

Decision: after generation, the validator runs (D03), then a judge call scores register and naturalness, stored on the cache row. Below threshold falls back to passage-only. A CLI lists rows with scores and rejects one, busting the cache.

Consequences: the first deliverable is fully automated with a human lever. Threshold is set after the first 10 generations are hand-reviewed.

## D22. FastAPI uses the service role with explicit user scoping; RLS stays on for the browser client

Status: accepted, 2026-09-17

Decision: FastAPI verifies the Supabase JWT, extracts user_id, and scopes every progress query in code. Connection pool via asyncpg and SQLAlchemy. RLS policies still exist so the browser's Supabase client (auth and Storage only) cannot read another user's rows.

Consequences: one rule, the browser never queries tables. A missed scope in code is a bug the tests must catch.

## D23. Tests from day one: pytest, Vitest, one Playwright play-through at 375px, GitHub Actions

Status: accepted, 2026-09-17

Decision: pytest against a Postgres service container with pgvector. Vitest with Testing Library for the runner state machine. One Playwright test in an iPhone viewport plays the lesson against a mock API and asserts XP and streak. 80 percent coverage gate on both sides. LLM and TTS mocked in CI; nightly real eval.

Consequences: the first deliverable's definition of done is an executable test.

## D24. Migrations are Alembic, owned by the API, run on Railway deploy

Status: accepted, 2026-09-17

Decision: Alembic autogenerates from SQLAlchemy models. The Railway start command runs upgrade head before uvicorn. RLS policies are plain SQL inside Alembic migrations. Supabase Auth's schema is untouched.

Consequences: one migration history.

## D25. PWA at MVP is an installable shell only

Status: accepted, 2026-09-17

Decision: manifest, icons, app-shell service worker. No offline lessons.

Consequences: Add to Home Screen works. Offline sync of attempts against server-authoritative state is a later feature.

## D26. Minor conventions

Status: accepted, 2026-09-17

UI chrome is English. Placeholder locked lessons are real rows with published false. uv for Python, pnpm for the web app. No em dashes in user-facing copy, comments, or docs.

## D27. Frontend stays Next.js App Router in apps/web

Status: accepted, 2026-09-17

Context: a later message asked for "just React" in a web/ folder. Asked directly, the owner confirmed the Next.js decision stands.

Decision: D08 and D14 unchanged.

## D28. UI references studied; design direction proposed

Status: proposed, 2026-09-17

Context: the owner asked for a study of Duolingo, LingQ, 80 Days, Brilliant, Bunpro, and Memrise. Findings are in docs/ui-references.md.

Decision: borrow generic patterns only (progress bar, bottom call to action, feedback sheet, vertical path, line-by-line reveal, tap-word gloss, tile bank). No assets, mascots, brand colors, or commercial fonts. Proposed direction: Nunito for UI, a serif for historical passage layers, deep indigo primary, ochre accent, paper cream card surface.

Consequences: the direction is the working default for the scaffold until the owner approves or changes it.

## D29. Corpus availability corrected: more of Rizal is public domain than D05 assumed

Status: accepted, 2026-09-17, amends D05

Context: during the ingest work, a search of Project Gutenberg found public-domain editions that the grilling session assumed did not exist. Verified ids: Noli in Spanish 47584, Tagalog (Poblete) 20228, English (Derbyshire) 6737. Fili in Spanish 30903, Tagalog 47629, English (Derbyshire, The Reign of Greed) 10676. Essays: Filipinas dentro de cien años in Spanish 14839 and English 35899, The Indolence of the Filipino in English 6885. Letter to the women of Malolos in Tagalog 17116.

Decision: the MVP corpus stays Noli only (the scaffold ingests all three languages), but the licensing check in D05 is already answered for the Fili and those essays: they are public domain on Gutenberg and can be ingested in a later plan by adding EditionSpec entries. Modern Tagalog translations of the essays and letters remain out of scope for copyright reasons.

Consequences: a Tagalog Fili lane is possible without a licensing question. Chapter counts differ between editions (docs/tech-debt.md item 10), so cross-language alignment stays manual for pinned passages.

## D30. Dev environment facts

Status: accepted, 2026-09-17

Docker is unavailable on the dev machine and pnpm 11 refuses Node 20. Postgres 16 with pgvector 0.8.6 was installed through apt and runs on localhost:5432. Node 22 LTS is installed under /opt/node22 and linked into /usr/local/bin; pnpm 9.15 is activated through corepack. CI uses a pgvector service container and Node 22, so local and CI match.

## D31. Review sessions and the practice-to-refill rule

Status: accepted, 2026-09-17

Context: D16 says zero hearts ends the lesson into a practice-to-refill flow, but did not define a session.

Decision: a practice session is the run of review answers within a 30 minute window. Every tenth answer in a session refills hearts to five. Review answers are recorded as exercise_attempts rows with kind = review, which is what the count reads. Completion of a lesson only counts attempts made after the previous completion, so a lesson cannot be re-completed for XP without playing it again.

Consequences: the refill is server-side and cannot be triggered by the client alone. The 30 minute window is a constant in progress/review.py, easy to tune.
