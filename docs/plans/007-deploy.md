# Plan 007: First deploy, Railway API and Postgres, Vercel web

Workflow phases 0 to 5. Status: in progress. Date: 2026-09-25. Run by an architect session with two Herdr workers (builder, reviewer); the architect runs the suites and the smoke test. Provisioning is the owner's (billable, account-bound); this plan takes over plan 003's open item 5.2.

Scope, grilled with the owner on 2026-09-25: everything up to the billable click for the first deploy. Railway project in the jacob-rafal workspace with Postgres (pgvector template), the API service and an audio bucket; Vercel hobby project for the web from the GitHub repo. Previews run in mock mode. The three Gutenberg source texts are committed so production ingests the exact files the hand alignment was built on. Audio stays on the fake engine (tech debt 14 open), so the first deploy ships lessons without audio.

## Phase 0: Setup

### Analysis

What exists. Plan 003 wrote apps/api/Dockerfile, railway.toml, .dockerignore and docs/deploy.md but never built the image on Railway. Four readers found the runbook does not work as written:
- Railway's default Postgres template has no pgvector and Railway will not add extensions, so the first migration's CREATE EXTENSION fails. The pgvector marketplace template (or a service on pgvector/pgvector:pg16, what CI uses) is required. docs/deploy.md and D33's context are wrong on this point.
- content/ is not in the image: the build context is apps/api and content/ sits at the repo root, although the Dockerfile sets CONTENT_DIR=/app/content. The seed cannot run in the container.
- The CMD runs migrations at every boot and every replica (a failed migration crash-loops instead of blocking the deploy) and uses plain `uv run`, which re-syncs the dev group over the network at startup.
- railway.toml is deprecated config: new services cannot opt into it, and it does not follow the root directory. Settings belong in the dashboard.
- The documented order runs `seed` after `render-audio`, which nulls every audio_url, because seed writes the YAML value. render-audio seeds on its own.
- The bucket reference names in the runbook do not exist (Railway exposes BUCKET, ACCESS_KEY_ID, SECRET_ACCESS_KEY, REGION, ENDPOINT), and the real S3 bucket name carries a hash, so the "audio" default is wrong.
- Railway's DATABASE_URL is postgresql:// and no sync driver is installed; the app and alembic need postgresql+asyncpg://.
- A missing SESSION_JWT_SECRET, LLM key or bucket credentials only fails on the first matching request; /health checks the database only.
- Ingest downloads Gutenberg texts when its expected file names are missing, and dev's cached files use different names; the hand-aligned passage refs are pure locators, so a changed text would silently shift paragraphs under every lesson.
- apps/web is a standalone pnpm project (no workspace), the generated types are committed so no API is needed at build time, one test imports packages/contracts from outside the root directory (keep Vercel's outside-root setting on), NEXT_PUBLIC values are inlined at build time, CI never runs `next build`, manifest.json lists two icons that do not exist, and Vercel may pick pnpm 10 for a v9 lockfile without a packageManager field.
- Tech debt 23 (content hash includes defaulted fields) is due before the first seed on Railway; tech debt 16 (SUPABASE_JWT_SECRET fallback) is due after the first deploy.

Decisions (D37). The API image is built from the repo root with a multi-stage uv Dockerfile that bakes content/ and runs non-root; migrations run in Railway's pre-deploy step, not the start command (supersedes D24's wording); Railway and Vercel deploy from main automatically, Railway waiting for CI; previews use mock mode; the corpus texts are committed under apps/api/data/raw with a checksum test; a `rizalai bootstrap` command runs ingest and seed idempotently with count checks under an advisory lock; render-audio runs locally when an engine exists and is never followed by a plain seed.

Owner steps (billable or account-bound, in order): create the Railway project rizal-ai in the jacob-rafal workspace; add Postgres from the pgvector template and enable Public Access (TCP proxy); add a bucket named audio; add the API service from JakeCob/rizal-ai with root directory empty, RAILWAY_DOCKERFILE_PATH=/apps/api/Dockerfile, pre-deploy command `alembic upgrade head`, healthcheck /health, wait-for-CI on; generate SESSION_JWT_SECRET; generate the API domain; create the Vercel project with root apps/web, Node 22, production env NEXT_PUBLIC_API_URL, preview env NEXT_PUBLIC_API_MODE=mock; paste the API and web domains and the OpenRouter key when ready. Agents then set the remaining variables through the Railway MCP, run the bootstrap over the proxy, run the smoke test, and rewrite the runbook with the real names.

### Behaviors

Container and settings:
- Given the repo root as build context, when the image builds, then /app/content holds every unit and lesson file, the venv has no dev packages, the process runs as a non-root user, and the start command is uvicorn alone on $PORT with proxy headers.
- Given DATABASE_URL in the postgresql:// or postgres:// scheme, when settings load, then it is rewritten to postgresql+asyncpg://.
- Given ENV=production with SESSION_JWT_SECRET empty, or CORS_ORIGINS empty, or AUDIO_STORE=s3 with any S3 credential empty, or LLM_PROVIDER=openrouter with no key, when the app starts, then it refuses to start with a message naming the variable.
- Given ENV=local, when the same variables are empty, then the app starts as today.
- Given CI, when a push or pull request runs, then the image builds from the repo root (docker build in CI; the dev machine has no docker) and the web build runs.

Corpus and bootstrap:
- Given the three committed texts, when a test hashes them, then each matches its pinned sha256, and ingest finds them by the names it expects without downloading.
- Given a migrated empty database, when `rizalai bootstrap` runs, then it ingests the three editions (skipping any edition whose row count already matches), seeds content, prints the counts, and exits non-zero if any ref is unresolved or the counts differ from the content's own totals; a second run changes nothing and exits zero.
- Given two bootstrap runs at once, when they start, then the second waits on the advisory lock.
- Given lessons already carrying audio URLs, when bootstrap seeds without an engine, then existing audio URLs are kept.
- Given the example lesson, when its content hash is computed, then it equals a pinned value and does not change when an optional field is added with its default (tech debt 23).

Web:
- Given a push that touches neither apps/web nor packages/contracts, when Vercel evaluates the ignore command, then the build is skipped; any other push builds.
- Given the manifest, when the browser fetches the icons, then both PNGs exist.
- Given apps/web/package.json, when Vercel installs, then pnpm 9 and Node 22 are pinned.

Smoke:
- Given a deployed API base URL and the web origin, when `rizalai smoke --base-url --origin` runs, then it checks /health, a preflight from the origin, POST /session/anonymous, GET /me, GET /tree with 8 lessons, GET /lessons/{first} and its passages, and reports each as pass or fail with the response detail, exiting non-zero on any failure.

### Phases of work and parallelism

- A. Container and settings (builder, api): Dockerfile from the repo root, root .dockerignore, railway.toml removed, URL scheme validator, production startup checks, S3 defaults, CI docker build job, tests. Reviewer reviews.
- B. Corpus and bootstrap (builder, api, after A): commit the three texts with the CLI's expected names, checksum test, `rizalai bootstrap`, keep-audio seed, tech debt 23 canonical hash with a pinned example hash, `rizalai smoke`. Reviewer reviews.
- C. Web deploy readiness (builder, web, after B): vercel.json ignore command, packageManager and engines, CI `pnpm build` step, manifest icons. Reviewer reviews.
- D. Docs (architect): this plan, D37, docs/deploy.md rewritten as the owner's step list plus the agents' wiring steps with placeholders only where a real name must come from the dashboard, docs/rollback.md, docs/architecture.md, tech debt (23 closed, 16 scheduled, 2 noted), plan 003's 5.2 handed over.
- E. Provisioning and wiring (owner then architect): owner creates the services; architect reads the real variable names through the Railway MCP, sets variables, watches the first deploy, runs bootstrap over the proxy, runs smoke, records the names in the runbook; owner opens the Vercel URL on the phone and plays a lesson.
- F. After the first deploy: remove the SUPABASE_JWT_SECRET fallback (tech debt 16) as a follow-up commit.

Dependencies: B after A (the Dockerfile must copy the corpus files too). C after B on the one builder. D in parallel. E after A to C are merged and pushed. F after E.

### File ownership

| Worker | Files |
|---|---|
| builder (A) | apps/api/Dockerfile, .dockerignore (root, new), apps/api/.dockerignore (removed or emptied), apps/api/railway.toml (removed), apps/api/src/rizalai/config.py, main.py, tests/unit/test_config.py, .github/workflows/ci.yml (api job and a new docker job) |
| builder (B) | apps/api/data/raw/*.txt (three committed files), .gitignore and apps/api/.gitignore (un-ignore them), apps/api/src/rizalai/cli.py, content/loader.py (content_hash), content/seed.py (keep audio), corpus/ingest.py (batching, skip-if-present), a new bootstrap module, a new smoke module, tests |
| builder (C) | apps/web/vercel.json (new), apps/web/package.json, apps/web/public/icon-192.png and icon-512.png (new), .github/workflows/ci.yml (web job) |
| reviewer | reads everything, edits nothing |
| architect | docs/plans/007-deploy.md, docs/plans/003-railway.md, DECISIONS.md, docs/deploy.md, docs/rollback.md, docs/architecture.md, docs/tech-debt.md |

## Phase 1: Document

Tech debt: closes 23; schedules 16 for the follow-up commit after the first deploy; 2 (RLS cleanup) becomes due once the production database exists and is carried to plan 008 with a tester. New: 28, the audio route calls boto3 synchronously inside an async handler; 29, the app configures no logging so INFO from rizalai.* never reaches Railway logs.

Rollback: a bad deploy is rolled back on Railway by redeploying the previous image; Vercel by promoting the previous deployment. Migrations are forward-only in production (the pre-deploy step blocks a deploy whose migration fails). A wrong variable is an env change and a redeploy. Bootstrap is idempotent; a partial ingest rolls back its edition.

## Phase 2: TDD plan

A. tests/unit/test_config.py: scheme rewrite; production startup checks per variable; local unaffected. The Dockerfile is proven by the CI docker job (no docker locally): the job builds the image from the repo root and runs `rizalai --help` and `python -c "import rizalai"` inside it, and lists /app/content/units.
B. tests/unit/test_corpus_files.py: the three files exist at the CLI's names with pinned sha256. tests/integration/test_bootstrap.py: bootstrap on an empty migrated database ingests fixture editions and seeds fixture content (small fixtures, not the real corpus), exits non-zero on unresolved refs, is idempotent, keeps audio URLs. tests/unit/test_content_loader.py: pinned example hash and a test that an added defaulted field leaves it unchanged. tests/unit/test_smoke.py: the smoke runner against the ASGI app reports each check.
C. CI runs `pnpm build`; a Vitest or script test is not needed for vercel.json, but the ignore command is exercised by hand in the report (git diff exit codes on two commits).

### Checklist

- [x] A. Container and settings: builder, reviewer
- [x] B. Corpus committed, bootstrap and smoke commands, canonical content hash: builder, reviewer
- [x] C. Web deploy readiness: builder, reviewer
- [x] D. Docs and D37: architect
- [~] E. Provisioning and wiring done through the Railway MCP on 2026-09-25 with the owner's approval (project, pgvector Postgres, bucket, API service, domain, variables, first deploy, bootstrap over railway ssh, smoke 6 of 6). Vercel project created and deployed on 2026-09-26 through the CLI with an owner token, production at https://rizal-ai.vercel.app (matches CORS_ORIGINS as set). Open: the GitHub app on the personal Vercel account for automatic deploys, "wait for CI" in the Railway dashboard, and the owner's phone play-through
- [ ] F. Remove the Supabase secret fallback after the first deploy (tech debt 16): builder, reviewer

## Phase 3 record

Same setup as plans 005 and 006. Exploration: four in-process readers (API packaging, Vercel readiness, data bootstrap, runbook state) and a read-only Railway inventory through the MCP (no RizalAI project exists; the jacob-rafal workspace is the target). Owner decisions: mock-mode previews, the corpus texts committed, the two deprecated deploy files deleted.

Review findings by task:
- A, container and settings: FIX on first review because local defaults counted as present in the production check (a forgotten CORS_ORIGINS or DATABASE_URL booted cleanly and failed later), AUDIO_BASE_URL and LLM_PROVIDER kept working-looking defaults, the test helper leaked the shell environment, and the CI docker job never ran the real start command. All fixed; RAILWAY_ENVIRONMENT now implies production when ENV is unset. Re-check MERGE. The image itself is proven only by the CI job (no docker on the dev machine).
- B, corpus and bootstrap: FIX on first review for a blocker that mattered: a routine content edit (a renamed slug or exercise key) would have cascade-deleted learner progress on an ordinary deploy with bootstrap reporting ok. Fixed with a learner-data guard that refuses and names the rows unless an explicit flag is passed, plus a dry run. Eight should-fixes applied: every digest verified before any write, refs resolved before the seed commits, embeddings on skipped editions, orphaned units, the re-versioning docstring naming the reflection cache, ingest downloading only on request, smoke never raising, and the test gaps. Re-check MERGE, with one test gap (the exercise-only deletion path of the guard) carried to the next small commit.
- C, web readiness: MERGE first time (ignore command exit codes shown for an api-only and a web commit, pinned pnpm and Node, icons rendered from the SVG, CI production build).

Results at the end of the agent phase:

| Suite | Result |
|---|---|
| API pytest | 286 passed, 89.4 percent coverage, ruff and mypy strict clean |
| Web Vitest, build | 72 passed, `pnpm build` green, lint and typecheck clean, Playwright 4 passed |
| CI | docker job (build from the repo root, real start command refuses without production variables, lesson files counted, non-root) and the web build step, both proven on the push |
| Bootstrap against the dev database | dry run: three editions skipped as present, 3 units, 8 lessons, 70 exercises, 0 unresolved refs, nothing written |
| Smoke against a local uvicorn | all checks pass; a patched 500 reports as a failed check |

Not done in the agent phase: provisioning, wiring, the real bootstrap and smoke, and the phone play-through (item E, waits on the owner); audio (tech debt 14); the RLS cleanup (tech debt 2, carried to plan 008).

## Phase 4: Review

- Commits on main, in order: 9d1c319 container and production settings with CI docker build (D37), 34c8427 web readiness, 01a8214 corpus, bootstrap, smoke and the canonical content hash, then the docs close-out. Pushed so the owner can provision from a green main.
- Docs: this plan; DECISIONS.md D37; docs/deploy.md rewritten as owner steps plus agent wiring steps with the production-check rules; docs/plans/003-railway.md item 5.2 handed over; docs/rollback.md deploy paths; docs/architecture.md migration line; docs/tech-debt.md row 23 closed, rows 28 (sync boto3 in an async route) and 29 (no app logging) added, row 16 scheduled for item F.
- Feature flag: none. The production checks are keyed on ENV or RAILWAY_ENVIRONMENT and change nothing locally.
- Knowledge share: `rizalai bootstrap --dry-run` before any production content change; never a plain seed after render-audio; the corpus files are the alignment's ground truth and their digests are pinned in code and tests.

## Phase 5: Retrospective

What worked:
- Reading the deploy surface before touching it. Every one of plan 003's deploy files had a defect that only a real build would have shown; the readers found them in an hour and the fixes shipped with tests instead of on Railway.
- The learner-data guard came from asking the reviewer what happens when content is removed. That question belongs in every plan that seeds production.
- Owner questions were three and early; the rest were lead calls recorded in D37.

What did not:
- The first production check treated local defaults as present. A guard that can pass on defaults is a guard against nothing; the review caught it, the brief should have said "unset, not blank".
- The image cannot be built on the dev machine, so a Dockerfile defect will surface on the push. Plan 008 should consider a container runtime on the dev box, or accept CI as the build check.
- Three reviews out of three were FIX on first pass. Deploy code is where the reviewer earns its keep; the sizing should assume a fix round per task.

Change for plan 008:
- After provisioning: remove the SUPABASE_JWT_SECRET fallback (tech debt 16), the RLS cleanup migration (tech debt 2), and app logging (tech debt 29), all small.
- Decide the audio path (tech debt 14): the deploy now makes the by-ear bake-off possible on the real phone URL.
- Consider a tester with docker for the container path.
- Add the missing test for the learner-data guard's exercise-only deletion path.
