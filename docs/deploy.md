# Deploy

Railway hosts the API, a Postgres service, and a storage bucket in one project (DECISIONS.md D33). Vercel hosts the web app (D11). Nothing here is automated yet; these are the steps for the first deploy.

## Railway project

1. Create a project named rizal-ai.
2. Add a Postgres service from the Railway template. Railway's Postgres ships the pgvector extension; the first migration runs `CREATE EXTENSION IF NOT EXISTS vector`.
3. Add a storage bucket named audio. Railway exposes it as S3-compatible storage with an endpoint, an access key id, a secret, and the bucket name.
4. Add the API service from the GitHub repo JakeCob/rizal-ai with root directory apps/api. The Dockerfile and railway.toml are picked up automatically. The container runs migrations, then uvicorn on $PORT, and Railway checks /health.

Variables on the API service (see .env.example at the repo root for every option):

```
ENV=production
DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/${{Postgres.PGDATABASE}}
SESSION_JWT_SECRET=<openssl rand -hex 32>
CORS_ORIGINS=https://<web domain>
CORS_ORIGIN_REGEX=https://<vercel project>-[a-z0-9-]+-<team>\.vercel\.app
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=<key>
EMBEDDINGS_PROVIDER=deepinfra
EMBEDDINGS_API_KEY=<key>
AUDIO_STORE=s3
S3_ENDPOINT_URL=${{audio.BUCKET_ENDPOINT}}
S3_BUCKET=${{audio.BUCKET_NAME}}
S3_ACCESS_KEY_ID=${{audio.BUCKET_ACCESS_KEY_ID}}
S3_SECRET_ACCESS_KEY=${{audio.BUCKET_SECRET_ACCESS_KEY}}
AUDIO_BASE_URL=https://<api domain>/audio
TTS_ENGINE=<winner of the bake-off>
```

The DATABASE_URL uses the private domain so traffic stays inside the project. Use the asyncpg scheme, not Railway's plain postgresql:// DATABASE_URL.

After the first deploy, from a shell on the service or locally with the public DATABASE_URL:

```
uv run rizalai ingest noli_es && uv run rizalai ingest noli_tl && uv run rizalai ingest noli_en
uv run rizalai render-audio --engine <winner>
uv run rizalai seed
```

## Vercel

Import the repo with root directory apps/web. Variables:

```
NEXT_PUBLIC_API_MODE=
NEXT_PUBLIC_API_URL=https://<api domain>
```

The browser calls the API cross-origin (D36), so the API's CORS_ORIGINS must list the Vercel production domain exactly (scheme and host, no trailing path). Preview deployments get per-deploy hostnames, which CORS_ORIGIN_REGEX admits; leave it empty to keep previews off the real API. Anchor the regex on the team suffix Vercel appends to preview hostnames (`-<team>.vercel.app`): a bare project prefix such as `https://rizal-ai-[a-z0-9-]+\.vercel\.app` also matches any other account's project named `rizal-ai-<anything>`, so the allowlist would stop meaning our deployments. Previews get the same API URL and only read and write the learner's own anonymous session.

## Rotation and rollback

Rotating SESSION_JWT_SECRET signs every learner out (their next visit becomes a new anonymous learner). Rolling back a deploy is a redeploy of the previous image on Railway; migrations are forward-only in production (docs/rollback.md).
