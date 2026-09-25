# Deploy

Railway hosts the API, a Postgres service and a storage bucket in one project (DECISIONS.md D33, D37). Vercel hosts the web app (D11, D36). Both deploy from main automatically once connected; Railway waits for CI. Plan 007 (docs/plans/007-deploy.md) is the first deploy. Steps marked "owner" create billable or account-bound resources; steps marked "agent" are run by the architect session with the Railway MCP and the CLI once the resources exist. The first deploy happened on 2026-09-25 through the Railway MCP; the real names are recorded below. Project rizal-ai (id 4d761190-0333-476c-86e7-73bee551fa9c) in the jacob-rafal workspace, environment production, region asia-southeast1 (Singapore); services pgvector (Postgres 18 with pgvector from template 3jJFCA, volume 50 GB, public TCP proxy shuttle.proxy.rlwy.net:34659), api (this repo, main), bucket audio (region sin). API domain: https://rizal-ai.up.railway.app.

## 1. Railway project (owner)

1. Create a project named rizal-ai in the jacob-rafal workspace.
2. Add Postgres from the pgvector template (railway.com/deploy/3jJFCA), not the default Postgres template: the default image has no extensions and the first migration runs `CREATE EXTENSION IF NOT EXISTS vector`. Enable Public Access (TCP proxy) on the database so the bootstrap can run from a laptop; it can be disabled again afterwards.
3. Add a storage bucket named audio. Each environment gets its own bucket and credentials. Railway exposes ENDPOINT, BUCKET, ACCESS_KEY_ID, SECRET_ACCESS_KEY and REGION as reference variables; the real S3 bucket name carries a hash, so never assume "audio".
4. Add the API service from the GitHub repo JakeCob/rizal-ai. Settings: root directory empty (the image is built from the repo root so content/ ships in it), Dockerfile path `/apps/api/Dockerfile` (variable RAILWAY_DOCKERFILE_PATH), watch paths `/apps/api/**` and `/content/**`, pre-deploy command `alembic upgrade head` with a timeout of about 300 seconds, healthcheck path `/health` with a 120 second timeout, restart policy on failure with 5 retries, and "wait for CI" on (a dashboard-only setting the MCP cannot set; still off as of the first deploy). The start command stays empty (the Dockerfile runs uvicorn). railway.toml is gone: Railway deprecated config files and they never followed the root directory.
5. Generate a domain for the API service (done: https://rizal-ai.up.railway.app, target port 8000).
6. Generate a session secret with `openssl rand -hex 32` and keep it as `<session secret>`.

## 2. API variables (agent, through the Railway MCP once the services exist)

```
ENV=production
DATABASE_URL=postgresql+asyncpg://${{pgvector.PGUSER}}:${{pgvector.PGPASSWORD}}@${{pgvector.PGHOST_PRIVATE}}:${{pgvector.PGPORT_PRIVATE}}/${{pgvector.PGDATABASE}}
SESSION_JWT_SECRET=<session secret>
CORS_ORIGINS=https://<web domain>
CORS_ORIGIN_REGEX=
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=<key, when the owner provides it; until then LLM_PROVIDER=fake>
AUDIO_STORE=s3
S3_ENDPOINT_URL=${{audio.ENDPOINT}}
S3_BUCKET=${{audio.BUCKET}}
S3_ACCESS_KEY_ID=${{audio.ACCESS_KEY_ID}}
S3_SECRET_ACCESS_KEY=${{audio.SECRET_ACCESS_KEY}}
S3_REGION=${{audio.REGION}}
AUDIO_BASE_URL=https://rizal-ai.up.railway.app/audio
PORT=8000
RAILWAY_DOCKERFILE_PATH=apps/api/Dockerfile
LOG_LEVEL=INFO
```

PORT is set explicitly to 8000 because the generated domain targets port 8000 (the Dockerfile's EXPOSE) while Railway otherwise assigns 8080. The bucket reference names ENDPOINT, BUCKET, ACCESS_KEY_ID, SECRET_ACCESS_KEY and REGION rendered correctly (the production check passed). CORS_ORIGINS was set to https://rizal-ai.vercel.app before the Vercel project existed; correct it once Vercel assigns the real production domain.

Notes. The settings rewrite a plain `postgresql://` URL to the asyncpg scheme, but composing it from the PG parts on the private domain keeps traffic inside the project. If you paste a public connection string instead, drop any `?sslmode=...` query: the settings rewrite the scheme but keep the query, and asyncpg rejects libpq's sslmode parameter. `pgvector` is the Postgres service's name as the dashboard shows it. Set ENV=production. If ENV is left unset, Railway's injected RAILWAY_ENVIRONMENT makes the API run as production anyway, and if ENV is set to anything else on Railway the API refuses to start. In production the API refuses to start, and names each variable, when SESSION_JWT_SECRET is empty; when CORS_ORIGINS lists only localhost origins or is unset; when DATABASE_URL is unset or points at localhost; when LLM_PROVIDER is not written out (LLM_PROVIDER=fake is accepted, for the first deploy before the OpenRouter key exists); when the chosen provider's key (OPENROUTER_API_KEY or ANTHROPIC_API_KEY) is empty; and, under AUDIO_STORE=s3, when any of S3_ENDPOINT_URL, S3_BUCKET, S3_ACCESS_KEY_ID or S3_SECRET_ACCESS_KEY is empty or AUDIO_BASE_URL is empty or points at localhost. EMBEDDINGS_* are not checked, because only the CLI uses them. The pre-deploy `alembic upgrade head` imports only the settings, not the app, so migrations run even when this check would stop the server; a deploy with a bad config migrates and then fails its healthcheck, naming the missing variable in the deploy logs. CORS_ORIGIN_REGEX stays empty because previews run in mock mode (D37); set it only when a preview must reach the real API, anchored on the scope suffix Vercel appends (for example `https://rizal-ai-(git-[a-z0-9-]+|[a-z0-9]{9})-<scope>\.vercel\.app`), knowing that a `.vercel.app` hostname can still be claimed by another account, so the regex narrows but does not prove ownership. Leave unset: TEST_DATABASE_URL, AUTH_JWKS_URL, EMBEDDINGS_*, TTS_ENGINE, ANTHROPIC_API_KEY. LOG_LEVEL defaults to INFO (plan 008); set WARNING to quiet the Railway logs.

## 3. First deploy and bootstrap (agent)

1. Connecting the GitHub source triggers the first deploy. The pre-deploy step runs the migrations; a failure blocks the deploy instead of crash-looping. Then `GET https://rizal-ai.up.railway.app/health` returns `{"status":"ok","db":"ok"}` on the empty schema. On 2026-09-25 the first deploy built in about a minute and all five migrations ran in pre-deploy.
2. Bootstrap inside the API container, where the content and the corpus texts are baked in and the private database domain resolves, with the Railway CLI logged in to an account on the workspace (no secret leaves Railway):

```
railway ssh -p 4d761190-0333-476c-86e7-73bee551fa9c -e 395aec36-7dfc-4777-a8a2-c4482dfdf1c3 -s api -- rizalai bootstrap
```

A pre-deploy command chained with `&&` did not run the bootstrap (only the first command ran), so the pre-deploy stays `alembic upgrade head` and the bootstrap is this explicit step; re-run it after every content change (it is idempotent and refuses learner-data loss without `--allow-learner-data-loss`). The local alternative over the TCP proxy still works with the public URL rewritten to the asyncpg scheme:

```
ENV=production DATABASE_URL=postgresql+asyncpg://<user>:<password>@shuttle.proxy.rlwy.net:34659/rizalai uv run rizalai bootstrap
```

It takes an advisory lock, checks the database is at the migration head, ingests the three committed Gutenberg texts (apps/api/data/raw, byte-identical to the files the hand alignment was built on; each edition is skipped when its rows already exist), seeds the content, and exits non-zero unless it ends with 3 units, 8 lessons, 70 exercises and 0 unresolved refs (numbers as of plan 007; the command reads the totals from the content itself). A second run changes nothing. Embeddings are left empty (nothing on the request path reads them); run with `--embed` and EMBEDDINGS_* set when retrieval for extras ships.
3. Smoke test from the same machine:

```
uv run rizalai smoke --base-url https://rizal-ai.up.railway.app --origin https://<web domain>
```

It checks /health, a CORS preflight from the web origin, POST /session/anonymous, GET /me, GET /tree (8 lessons), and the first published lesson with its passages, and exits non-zero on any failure. On 2026-09-25 it passed 6 of 6 after the bootstrap (12,114 passages, 3 units, 8 lessons, 70 exercises, 0 unresolved refs).
4. Audio: only after the TTS bake-off (tech debt 14). Run `rizalai render-audio --engine <winner>` locally with the S3 variables and AUDIO_BASE_URL set; it renders into the bucket and seeds on its own. After that, never run a plain `seed` or `bootstrap` seed step against production without an engine: the bootstrap keeps existing audio URLs, but render-audio is the command that changes content once audio exists.

## 4. Vercel project (owner)

1. Import JakeCob/rizal-ai as a Hobby project. Root directory `apps/web`, framework Next.js, install `pnpm install --frozen-lockfile`, build `pnpm build`, Node 22.x. Keep "Include files outside the Root Directory in the Build Step" on (a test imports packages/contracts). apps/web/package.json pins pnpm 9 through packageManager; set ENABLE_EXPERIMENTAL_COREPACK=1 so Vercel honours it. apps/web/vercel.json skips builds for pushes that touch neither apps/web nor packages/contracts.
2. Production environment variables: `NEXT_PUBLIC_API_URL=https://rizal-ai.up.railway.app` (https, no trailing slash); leave NEXT_PUBLIC_API_MODE unset.
3. Preview environment variables: `NEXT_PUBLIC_API_MODE=mock` (previews play the fixture lesson and never touch the production database). NEXT_PUBLIC_API_URL may be omitted.
4. Note the production domain Vercel assigns as `<web domain>` and give it to the agent for CORS_ORIGINS. NEXT_PUBLIC values are inlined at build time: changing either needs a redeploy without the build cache.
5. Open `https://<web domain>` on the phone, start a lesson, and play it through. The service worker registers for the first time on this deploy (D25); a stale shell is fixed by the next deploy because the cache is network-first.

## 5. Rotation and rollback

Rotating SESSION_JWT_SECRET signs every learner out (their next visit becomes a new anonymous learner). Rolling back a deploy is a redeploy of the previous image on Railway, or promoting the previous deployment on Vercel. Migrations are forward-only in production. A CORS error on one endpoint while the others work usually means that endpoint returned an unhandled 500; read the API logs before touching the origin variables (docs/rollback.md).
