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
| GET | /me | yes | creates the users row on first call, regenerates hearts, reads X-Timezone |
| GET | /tree | yes | units and lessons with locked, active, done status |
| GET | /lessons/{id} | yes | whole lesson including answers, for local grading |
| GET | /lessons/{id}/reflection | yes | passage layers plus the cached or freshly generated reflection |
| POST | /attempts | yes | one answer, graded server-side, spends a heart when wrong |
| POST | /lessons/{id}/complete | yes | re-grades attempts since the last completion, awards XP, streak, FSRS |
| GET | /review/due | yes | up to ten due review items |
| POST | /review/answer | yes | reschedules through FSRS, refills hearts every ten answers |
| GET | /audio/{file} | no | pre-rendered audio when AUDIO_STORE=local |

## Commands

```
uv run rizalai seed                                   # content/ YAML to Postgres, idempotent
uv run rizalai export-contracts ../../packages/contracts/schema.json
uv run rizalai ingest noli_tl                         # also noli_es, noli_en; downloads and caches the text
uv run rizalai tts-bakeoff --lines 3                  # samples/tts/<engine>-NN.*, listen on a phone
uv run rizalai render-audio --engine fake             # render every line, then re-seed audio urls
uv run rizalai reflections list                       # cached reflections with status and scores
uv run rizalai reflections reject <cache id>          # bust one so the next request regenerates
```

```
uv run rizalai eval-reflection --models anthropic/claude-opus-5,qwen/qwen3.8-max-0902
uv run rizalai eval-summary ../../evals/reflection/results/<run>   # after filling scores.csv
```

Provider switches, all defaulting to fakes so a fresh checkout runs with no keys: LLM_PROVIDER (fake, openrouter, anthropic; OpenRouter is production, D32), EMBEDDINGS_PROVIDER (fake, deepinfra), TTS_ENGINE (fake, mms, xtts, google), AUDIO_STORE (local, supabase).
