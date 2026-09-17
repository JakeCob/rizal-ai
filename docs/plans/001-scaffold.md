# Plan 001: Scaffold

Workflow phases 0 to 2 for the scaffold. Status: in progress. Date: 2026-09-17.

Scope, fixed by the owner: FastAPI backend with health check, database connection, and GET /lessons/{id} returning a placeholder lesson. Next.js frontend with the skill tree screen and the exercise runner shell. Ingestion script for Noli into source_passages with embeddings. Nothing else. The authored Chapter 1 lesson and the reflection endpoint are plan 002.

## Phase 0: Setup

### Analysis

The scaffold proves plumbing, not content. Every piece is a thin vertical slice: a YAML lesson file seeds Postgres, the API serves it under auth, the web app renders it in the tree and plays it in the runner, and the ingest script fills source_passages from Gutenberg text. The placeholder lesson is labeled as such and is replaced in plan 002.

Environment facts that shape the plan:
- No docker on this machine. A local Postgres 16 with pgvector 0.8.6 was installed via apt and is running on port 5432 with databases rizalai and rizalai_test. Tests use it directly; CI uses a service container.
- No Supabase, Anthropic, or embeddings credentials in the environment. Every external client has a fake used by tests and by local runs without keys. Real credentials are the owner's to add.
- pnpm 11 refuses Node 20; pnpm 9.15 is activated via corepack. CI pins Node 22.
- The local Postgres has no auth schema, so the users table cannot hold a foreign key to auth.users in a migration that must run locally. Row Level Security policies are written in a separate migration that no-ops when the auth schema is absent. Tech debt item 1.

### Behaviors for the scaffold

Given, When, Then. These become test names.

API:
- Given the API is running, when GET /health is called, then 200 with {status: ok, db: ok} and no auth is required.
- Given no Authorization header, when GET /lessons/{id} is called, then 401.
- Given an invalid or expired JWT, when GET /lessons/{id} is called, then 401.
- Given a valid JWT and a seeded lesson, when GET /lessons/{id} is called, then 200 with a body that validates against the Lesson contract, including vignette beats, exercises with answers, and source_passage_ids.
- Given a valid JWT and an unknown id, when GET /lessons/{id} is called, then 404.
- Given a valid JWT for a user with no users row, when any authed endpoint is called, then a users row is created with default hearts 5, xp 0, streak 0.
- Given a valid JWT, when GET /tree is called, then units and lessons in order, with the first published lesson active and unpublished lessons locked.
- Given the content directory, when the seed script runs twice, then lessons and exercises exist once, and lesson_version equals the content hash.

Contracts:
- Given the Pydantic models, when the export script runs, then packages/contracts/schema.json is written and the web types file is regenerated with no diff on a second run.

Web:
- Given the tree endpoint, when the tree page renders at 375px, then unit headers and lesson nodes appear, the active node is focusable and labeled, locked nodes are labeled locked, and nothing scrolls horizontally.
- Given the active node is tapped, when the popover opens, then it shows title, minutes, XP, and a Start link to the lesson route.
- Given a lesson is loaded, when the runner mounts, then the first vignette line is shown and a Continue button advances through lines.
- Given the vignette ends, when exercises begin, then each of the four exercise types renders its component from the payload, with a check button that grades locally and shows a green or red feedback sheet.
- Given the last exercise is checked, when Continue is tapped, then a completion screen shows the XP total for the session (not persisted in this plan).
- Given the runner, when transitions happen, then no network request is made between exercises.

Ingest:
- Given a Gutenberg plain-text Noli file, when the parser runs, then chapters are detected and paragraphs are split with char offsets that reproduce the original text when sliced.
- Given parsed paragraphs, when ingest runs against the database, then rows exist per (work, language, chapter, paragraph_index) with translator and license_note, and a second run inserts nothing new.
- Given rows without embeddings, when the embed step runs with the fake embedder, then dense and sparse columns and embedding_model are filled.
- Given the real embedder is configured, when one passage is embedded, then the request shape matches the hosted bge-m3 API. Verified by a recorded fixture, not a live call, in CI.

### Phases of work

1. API foundation: project, settings, database session, Alembic initial migration, health endpoint, test harness.
2. Auth: JWT verification (HS256 secret or JWKS), user upsert dependency.
3. Contracts: Pydantic models for Lesson, Beat, Exercise union, Tree. Export to JSON Schema and TypeScript.
4. Content seed: YAML loader, validation, placeholder lesson, seed script, GET /lessons/{id}, GET /tree.
5. Web foundation: Next.js app, Tailwind tokens, shadcn/ui base, Supabase auth bootstrap, API client, TanStack Query.
6. Web tree screen.
7. Web runner shell: vignette player, four exercise components, local grading, feedback sheet, completion screen.
8. Playwright smoke at 375px against a mocked API.
9. Ingest: Gutenberg parser, ingest command, embedder protocol with fake and bge-m3 adapters.
10. CI workflow, PWA manifest, README.

### Dependencies

- 3 before 4 and before 5 (web types come from contracts).
- 1 before 2 before 4.
- 4 before 6 and 7 for real data; 6 and 7 can start against the contract's example payloads.
- 1 before 9 (ingest uses the same models and session).
- 10 last.

### Review of Phase 0

Risks: the exercise contract is the one thing that is expensive to change later, because content YAML, DB rows, API, and four React components all depend on it. It gets the most review. Everything else is replaceable.

## Phase 1: Document

Docs produced by this plan: this file, apps/api/README.md, apps/web/README.md, packages/contracts/README.md, root README.md. docs/architecture.md is updated at the end if anything drifted.

### Tech debt log (docs/tech-debt.md is created with these)

1. users.id has no foreign key to auth.users locally. Add the constraint in a Supabase-only migration once a project exists.
2. RLS policies migration is a no-op without the auth schema. Verify against Supabase before first deploy.
3. Placeholder lesson content is scaffolding, replaced in plan 002.
4. Sparse vector stored as jsonb, with no index. Add a GIN index or a proper sparse index when retrieval is exercised.
5. Web runner completion is not persisted in this plan. POST /attempts and POST /lessons/{id}/complete are plan 002.
6. No audio in the scaffold; audio_url is nullable and the player renders a disabled control when null. Plan 002 renders audio.

### Rollback

No production exists. Rollback is git revert of the plan's commits. Database rollback is alembic downgrade base against local or Supabase. Ingest is idempotent and can be cleared with DELETE FROM source_passages WHERE work = 'noli'.

## Phase 2: Plan TDD

Test layout:
- apps/api/tests/unit: contracts, YAML loader, parser, hash, embedder fakes. No database.
- apps/api/tests/integration: endpoints and seed against rizalai_test with a per-test transaction rollback.
- apps/web: Vitest unit tests for the runner reducer, grading functions, and each exercise component with Testing Library. Playwright e2e/lesson.spec.ts at iPhone 13 viewport against route-mocked API responses.

Order per phase: write the failing test, run it, show red, implement, run green, refactor, run again.

Coverage gates: pytest-cov 80 percent on src/rizalai, Vitest 80 percent on components and lib.

### Checklist

- [ ] 1.1 uv project, ruff, mypy, pytest config
- [ ] 1.2 Settings from env with a .env.example
- [ ] 1.3 Async engine and session, test harness with transaction rollback
- [ ] 1.4 SQLAlchemy models for all nine tables
- [ ] 1.5 Alembic initial migration, plus RLS migration guarded on auth schema
- [ ] 1.6 GET /health with db check, test red then green
- [ ] 2.1 JWT verification for HS256 and JWKS, tests with minted tokens
- [ ] 2.2 current_user dependency that upserts users
- [ ] 3.1 Pydantic contracts: Beat, four exercise payloads, Exercise union, Lesson, TreeUnit, TreeLesson, Tree
- [ ] 3.2 Export script to schema.json and TypeScript, idempotent test
- [ ] 4.1 YAML loader with validation and content hash
- [ ] 4.2 Placeholder lesson YAML, labeled
- [ ] 4.3 Seed command, idempotent test
- [ ] 4.4 GET /lessons/{id} 200, 401, 404 tests
- [ ] 4.5 GET /tree with status computation
- [ ] 5.1 Next.js app, Tailwind tokens from D28, shadcn init
- [ ] 5.2 Supabase browser client, anonymous sign-in bootstrap
- [ ] 5.3 API client with typed responses, TanStack Query provider
- [ ] 6.1 Tree page with unit bands, nodes, popover, tests
- [ ] 7.1 Runner reducer and grading, tests
- [ ] 7.2 Vignette player
- [ ] 7.3 Four exercise components
- [ ] 7.4 Feedback sheet and completion screen
- [ ] 8.1 Playwright smoke at 375px
- [ ] 9.1 Gutenberg parser with fixture and offset round-trip test
- [ ] 9.2 Ingest command, idempotent test
- [ ] 9.3 Embedder protocol, fake, bge-m3 adapter with recorded fixture
- [ ] 10.1 GitHub Actions: api, web, e2e jobs
- [ ] 10.2 PWA manifest and icons
- [ ] 10.3 READMEs
- [ ] Scope check against this file
- [ ] Self review, security scan (ruff S rules, pnpm audit), perf check (runner transition timing in Playwright)
