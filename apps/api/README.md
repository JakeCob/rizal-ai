# RizalAI API

FastAPI backend. Python 3.12, uv, SQLAlchemy async, Alembic, pgvector.

## Run locally

Needs a Postgres with the pgvector extension. Locally that is the apt-installed Postgres 16 on port 5432 with databases `rizalai` and `rizalai_test`.

```
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run rizalai seed
uv run uvicorn rizalai.main:app --reload
```

Then `GET http://localhost:8000/health`. Authed endpoints need a Supabase access token as a Bearer header. Without a Supabase project, set `SUPABASE_JWT_SECRET` in `.env` and mint a token with the helper in `tests/helpers.py`.

## Test

```
uv run pytest          # runs migrations against rizalai_test, 80 percent coverage gate
uv run ruff check src tests alembic
uv run mypy
```

## Commands

```
uv run rizalai seed                                   # content/ YAML to Postgres, idempotent
uv run rizalai export-contracts ../../packages/contracts/schema.json
```

## Layout

```
src/rizalai/
  main.py        app factory, /health
  config.py      settings from env
  auth/          Supabase JWT verification, current_user dependency
  contracts/     Pydantic contracts, JSON Schema export
  content/       YAML loader, hashing, stable ids, seed
  lessons/       GET /lessons/{id}, GET /tree
  users/         GET /me
  db/            models, session
alembic/         migrations
tests/           unit (no db), integration (real db, rolled back per test)
```

## Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | /health | no | db check |
| GET | /me | yes | creates the users row on first call |
| GET | /tree | yes | units and lessons with locked, active, done status |
| GET | /lessons/{id} | yes | whole lesson including answers, for local grading |
