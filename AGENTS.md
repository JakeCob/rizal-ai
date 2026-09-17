# AGENTS.md

Instructions for AI coding agents working in this repo. CLAUDE.md imports this file. Keep it short and operational; the reasoning lives in the linked docs.

## Read first

- SPEC.md: what the product is, non-negotiables, acceptance behaviors.
- DECISIONS.md: numbered decisions. Do not re-litigate one silently; add a superseding entry.
- docs/architecture.md: repo layout, data model, request flows.
- docs/plans/: one plan per feature, phases 0 to 5. The current plan's checklist is the source of truth for what is in flight.

## Workflow for any feature or fix

Every task follows the owner's Complete Engineering Workflow v2.0:

1. Phase 0 Setup: analyze, write behaviors as Given/When/Then, define phases and dependencies, review.
2. Phase 1 Document: plan doc under docs/plans/, entries in docs/tech-debt.md and docs/rollback.md.
3. Phase 2 Plan: TDD plan and a checklist in the plan doc.
4. Phase 3 Implement: red (write the failing test, run it, show the failure), green (implement, run), refactor (self review, security scan, perf check). Scope check against the plan.
5. Phase 4 Review: code review, update docs, feature flag if the change warrants gating, knowledge share note.
6. Phase 5 Retrospective at the end of the plan doc.

Tests fail first. Show the failing output before implementing. Report anything skipped as skipped.

## Non-negotiables (from SPEC.md)

- No hallucinated Rizal. A byline attaches to spans, and every span must be a verbatim substring of a source_passages row, checked by code.
- Generated Tagalog that reads as translated English is a failure.
- Mobile-first at 375px. Exercise transitions under 200ms perceived.
- Keyboard and screen reader accessible. Audio for every vignette line.
- No em dashes anywhere: not in copy, comments, docs, or commit messages. Use commas, colons, or parentheses.

## Commands

API (apps/api, Python 3.12, uv):

```
uv sync
uv run alembic upgrade head
uv run rizalai seed
uv run rizalai export-contracts ../../packages/contracts/schema.json
uv run pytest            # migrations run against rizalai_test, 80 percent gate
uv run ruff check src tests alembic && uv run ruff format src tests alembic
uv run mypy
uv run uvicorn rizalai.main:app --reload
```

Web (apps/web, Node 22, pnpm 9):

```
pnpm install
pnpm gen:types           # after any contract change
pnpm dev                 # mock mode by default, see .env.example
pnpm test                # Vitest, 80 percent gate
pnpm test:e2e            # Playwright, iPhone viewport, mock API
pnpm lint && pnpm typecheck
```

Local Postgres 16 with pgvector runs on localhost:5432 with databases rizalai and rizalai_test (user postgres, password postgres). Docker is not available on the dev machine.

## Conventions

- Contracts change in apps/api/src/rizalai/contracts first, then export, then regenerate web types. CI fails on drift in either file.
- Content is YAML under content/units/. Lesson and exercise ids are uuid5 of slugs and keys; never hand-write ids.
- The browser never queries Supabase tables. All data goes through FastAPI. The Supabase client in the web app is for auth and Storage only.
- Every FastAPI query touching learner data filters on the current user's id in code.
- External clients (LLM, embeddings, TTS) sit behind a protocol with a fake. Tests never call the network.
- shadcn here is the Base UI flavor: triggers take a render prop, not asChild.
- Commit messages: conventional prefix (feat, fix, docs, chore, test), body explains what and why. Author is JakeCob.
- The user is less deep on Next.js than on Python. Explain frontend decisions in PR descriptions and READMEs.

## Do not

- Do not silently substitute a stack choice. Raise it, then wait.
- Do not modernize Poblete's 1909 Tagalog and present it as Rizal's text.
- Do not add a dependency on the request path for anything that can be prefetched or pre-rendered.
- Do not push to a remote unless asked. Pushes go to JakeCob/rizal-ai as JakeCob.
