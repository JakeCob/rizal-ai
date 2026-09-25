# RizalAI Architecture

Status: proposed, awaiting review. Date: 2026-09-17.

RizalAI teaches Tagalog and Rizal's literature together, Duolingo Stories style, with Rizal's world as the story spine. This document is the source of truth for repo layout, data model, and the decisions behind them. Update it whenever a decision changes.

## 1. Repo layout

Monorepo. One PR touches both sides of a feature and the lesson contract cannot drift.

```
rizal-ai/
  apps/
    api/                    FastAPI, Python 3.12, uv
      src/rizalai/
        main.py             app factory, health, routers
        config.py           pydantic-settings, all env vars
        db/                 SQLAlchemy models, async session, Alembic
        auth/               session issuing and JWT verification
        lessons/            lesson read model, seed loader
        progress/           attempts, completion transaction, hearts, streak
        srs/                FSRS scheduling over review_queue
        corpus/             source_passages retrieval (metadata, dense, sparse)
        generation/         reflection pipeline, validator, judge, cache
        providers/          LLMClient, EmbeddingsClient, TTSClient protocols
                            plus one adapter per vendor
      scripts/
        ingest_noli.py      Gutenberg text to source_passages
        seed_content.py     content/ YAML to units/lessons/exercises
        render_audio.py     vignette lines to the audio store (local or Railway bucket)
        tts_bakeoff.py      3 lines x 3 engines to samples/
        llm_eval.py         5 passages x N models, blind grading sheet
      alembic/
      tests/
    web/                    Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui, pnpm
      app/
        (auth)/             anonymous session bootstrap
        tree/               skill tree screen
        lesson/[id]/        exercise runner
      components/
        runner/             one component per exercise type, state machine
        tree/
      lib/
        api.ts              typed fetch client over FastAPI
        session.ts          anonymous session from the API
        types.generated.ts  from packages/contracts, do not edit
      e2e/                  Playwright, iPhone viewport
      public/manifest.json
  content/
    units/
      01-noli-arrival/
        unit.yaml
        01-capitan-tiago-dinner.yaml
    characters/noli.yaml    fixed vocabulary for tagging
  packages/
    contracts/              JSON Schema exported from Pydantic, consumed by web
  evals/
    reflection/             passages, rubric, results
  docs/
    architecture.md         this file
    tech-debt.md
    rollback.md
  .github/workflows/ci.yml
```

Why a thin client: the Next.js app is the phone app binary and FastAPI is the API. The browser never queries tables. Business logic lives in one language.

## 2. Content lanes

Two lanes with a hard boundary.

- Authored spine: YAML files under content/, validated by Pydantic, seeded to Postgres. Git is the review tool. lesson_version is a content hash.
- AI extras: generated at request time, grounded in source_passages, cached per lesson version, gated by a validator.

The byline rule, stated precisely: a byline attaches to spans, not paragraphs. Every span shown as Rizal's words must be a verbatim substring of a source_passages row and carry that row's id. The card header reads "In Rizal's voice" with a visible note that the reflection is generated from cited passages.

Which Tagalog learners drill: our own modern adaptation of each scene. Poblete's 1909 translation is shown only on the card, labeled as a 1909 translation, next to Rizal's Spanish and Derbyshire's English. Modernized Poblete is never presented as Rizal's text.

## 3. Data model

All ids are uuid unless noted. Timestamps are timestamptz. Learner ids are minted by the API when an anonymous session is created (D33).

### Identity and state

```
users
  id                 uuid pk, minted at POST /session/anonymous
  timezone           text            IANA, captured from browser on first session
  total_xp           int             default 0
  streak_count       int             default 0
  last_activity_date date            local date in users.timezone
  hearts             int             default 5
  hearts_updated_at  timestamptz     lazy regen: +1 per 4h computed on read
  current_unit_id    uuid null
  created_at
```

### Authored spine

```
units
  id, slug unique, title, order_index int, created_at  (no published flag: a unit is visible whenever it is in content, D35)

lessons
  id, unit_id fk, slug unique, title, order_index int
  version            text            content hash of the YAML
  published          bool            false = locked placeholder in the tree
  vignette           jsonb           [{line_id, speaker, tl, en, audio_url}]
  grammar_focus      text[]
  target_vocab       jsonb
  source_passage_ids uuid[]          pinned passages for the card
  created_at, updated_at

exercises
  id, lesson_id fk, order_index int
  type               text            sentence_assembly | translate_line | listen_tap | comprehension_mc
  payload            jsonb           discriminated on type, schema in packages/contracts
  answer             jsonb           answer_tokens or correct_index, plus accepted_orders (D34); ships to client for local grading, re-graded on completion
  xp                 int             default 10
  created_at
```

Exercise payload is a discriminated union. word_picture is a future variant, not a schema change.

### Corpus

```
source_passages
  id
  work               text            noli | fili | essay | letter
  language           text            es | tl | en
  translator         text null       poblete_1909 | derbyshire_1912 | null for Rizal's own
  chapter            int
  paragraph_index    int
  passage_group_id   uuid null       links aligned rows across languages
  text               text
  char_start, char_end int           offsets into the cleaned source file
  tags               jsonb           {characters:[], setting, speaker}
  tag_source         text            llm | human
  embedding          vector(1024)    bge-m3 dense
  sparse             jsonb           bge-m3 lexical weights {token_id: weight}
  embedding_model    text            for re-indexing
  license_note       text            source URL and public-domain basis
  unique (work, language, chapter, paragraph_index)
```

A passage is allowed to have no Tagalog variant. Alignment is manual for pinned passages at MVP; automated alignment is a later script that fills passage_group_id.

### Progress

```
exercise_attempts
  id, user_id fk, exercise_id fk, lesson_id fk
  correct            bool
  response           jsonb
  duration_ms        int
  created_at
  index (user_id, lesson_id, created_at)

user_progress
  user_id fk, lesson_id fk           pk
  attempts           int
  completed_at       timestamptz null
  best_score         numeric
  xp_earned          int
  lesson_version     text            version completed against

review_queue
  id, user_id fk, exercise_id fk     unique (user_id, exercise_id)
  due_at             timestamptz
  stability          float           FSRS
  difficulty         float           FSRS
  last_review        timestamptz
  reps, lapses       int
  state              text            new | learning | review | relearning
```

### Generation

```
generated_content_cache
  id
  kind               text            reflection | hint | drill
  cache_key          text unique     sha256 of (kind, lesson_id, lesson_version, prompt_version, model)
  content            jsonb           {tl, en, quoted_spans:[{text, passage_id}]}
  citations_valid    bool            every quoted span is a verbatim substring of its passage
  judge_score        numeric null
  status             text            published | rejected | fallback
  model, prompt_version, created_at
```

## 4. Request flows

Session: the browser calls POST /session/anonymous on first visit, keeps the token in localStorage, and sends it as a Bearer header on every call. Account linking is a later feature. The call is cross-origin (web on Vercel, API on Railway): the API allows the origins in CORS_ORIGINS plus an optional CORS_ORIGIN_REGEX for preview hostnames, with the Authorization, Content-Type and X-Timezone headers and no credentials (D36).

Lesson start: GET /lessons/{id} returns the whole lesson, exercises with answers, audio URLs, and the pinned passages. The client fires GET /lessons/{id}/reflection in parallel so the card is ready before the last exercise. Every exercise transition is local state.

Per answer: POST /attempts, fire and forget, optimistic UI. Grading is local against the shipped answer key.

Completion: POST /lessons/{id}/complete runs one transaction: re-grade attempts, award XP, update streak in the learner's timezone, spend hearts, upsert user_progress, seed review_queue via FSRS. Server is the source of truth for every number the learner sees persist.

Reflection: cache lookup by key. On miss, retrieve pinned passages plus 3 style-context passages, one structured Claude Opus 5 call returning {tl, en, quoted_spans}. Validator checks each quoted span is a verbatim substring of its cited passage; on failure regenerate once, then fall back to a passage-only card. Judge call scores register and naturalness. Row is published if citations are valid and score meets threshold, else fallback. A CLI command lists rows and rejects one, which busts the cache.

Hearts at zero: runner exits to a practice screen that plays due review_queue items and refills hearts to 5.

## 5. Decisions (ADR list)

1. Drilled Tagalog is our modern adaptation; Poblete 1909 is quarantined to the byline card.
2. Reflection is bilingual, Tagalog written first, one structured call, cached per lesson version, prefetched at lesson start.
3. Byline attaches to spans; each span must be a verbatim substring of a source_passages row.
4. Corpus MVP is Noli only in es, tl (Poblete), en (Derbyshire). Fili, essays, and letters wait on a per-work licensing check; Tagalog translations of the latter are likely still under copyright.
5. Superseded by D33: the API issues anonymous session tokens; a provider for account linking comes later.
6. Authored spine is YAML in the repo, seeded to Postgres. lesson_version is a content hash.
7. Monorepo with apps/api, apps/web, content/, packages/contracts.
8. LLM default is Claude Opus 5 via the Anthropic Python SDK behind an LLMClient protocol. An eval harness compares Claude, SEA-LION v3, and Qwen 3 on 5 Noli passages, graded blind. Provider is a config value.
9. Embeddings are bge-m3 via a hosted inference API, dense in pgvector and sparse in jsonb, model name stored per row.
10. Web on Vercel; API, Postgres, and the audio bucket in one Railway project (D33).
11. TTS is pre-rendered at seed time into a Railway bucket keyed by content hash, served by the API at /audio/{key}. A bake-off script renders 3 lines with MMS-TTS Tagalog, XTTS v2, and Google fil-PH; the engine is chosen by ear on a phone.
12. Exercise types at MVP: sentence_assembly, translate_line, listen_tap, comprehension_mc. word_picture deferred until there is an illustration pipeline.
13. Thin client: browser calls FastAPI with the session token, whole lesson fetched at start, TanStack Query.
14. Server-authoritative progress: per-attempt events, transactional completion, local grading re-checked on the server.
15. Hearts: 5, minus 1 per wrong answer, lazy regen 1 per 4 hours, zero ends the lesson into a practice-to-refill flow.
16. Streak: learner timezone on profile, extends on first completion of the local day.
17. SRS is FSRS via py-fsrs with default parameters.
18. Passage alignment: one row per language paragraph, optional passage_group_id, manual alignment for pinned passages only.
19. Character tags: LLM-tagged at ingest against a fixed character list, tag_source recorded, hand-corrected for pinned passages.
20. Quality gate: citation validator (hard), judge score (threshold), one-command reject.
21. FastAPI scopes every learner query by user_id in code. The browser never talks to the database, only to the API (D22 as amended by D33).
22. Tests: pytest against a Postgres service container, Vitest for the runner, one Playwright play-through at 375px against a mock API. GitHub Actions on every PR, 80 percent coverage gate, LLM and TTS mocked in CI, nightly real eval.
23. Migrations: Alembic, run on Railway deploy before uvicorn.
24. PWA at MVP: manifest, icons, app-shell service worker. No offline lessons.
25. Minor: UI chrome is English; placeholder lessons are real rows with published false; uv and pnpm.

## 6. First deliverable

Playable on a phone browser, end to end:

- Skill tree with Noli Chapter 1 unlocked and placeholder locked lessons after it.
- Lesson with 6 to 10 exercises across the four types, audio on every vignette line.
- "In Rizal's voice" card populated by the reflection pipeline from real Chapter 1 text, citations validated.
- XP awarded, streak incremented, progress persisted across reload.

Build order, fixed: this doc, then scaffold (API health and /lessons/{id} mock, web tree and runner shell, Noli ingest), then author the Chapter 1 lesson and wire the reflection endpoint.

## 7. Open items

- Licensing check for Fili and the essay and letter translations before any ingest beyond Noli.
- TTS engine, pending the bake-off.
- LLM provider, pending the eval harness.
- Judge score threshold, to be set after the first 10 generations are reviewed by hand.
