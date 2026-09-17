# RizalAI

Learn Tagalog through the world of Jose Rizal. A Duolingo Stories style app whose story spine is the Noli, the Fili, and Rizal's essays and letters.

- Product spec: [SPEC.md](SPEC.md)
- Decisions: [DECISIONS.md](DECISIONS.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- UI references: [docs/ui-references.md](docs/ui-references.md)
- Plans: [docs/plans/](docs/plans/)

## Layout

```
apps/api        FastAPI, Python 3.12, uv           see apps/api/README.md
apps/web        Next.js 15, TypeScript, pnpm       see apps/web/README.md
content/        authored lessons as YAML, seeded to Postgres
packages/       contracts: JSON Schema shared by api and web
docs/           architecture, plans, tech debt, rollback
```

## Quick start

Backend needs Postgres 16 with pgvector on localhost:5432 (databases `rizalai` and `rizalai_test`).

```
cd apps/api && cp .env.example .env && uv sync && uv run alembic upgrade head && uv run rizalai seed && uv run uvicorn rizalai.main:app --reload
cd apps/web && cp .env.example .env.local && pnpm install && pnpm dev
```

The web app starts in mock mode and needs no backend or credentials. Open http://localhost:3000 in a phone-sized viewport.

## Non-negotiables

No hallucinated Rizal. Tagalog that does not read as translated English. Mobile-first at 375px. Exercise transitions under 200ms. Keyboard and screen reader accessible. No em dashes in copy or comments.
