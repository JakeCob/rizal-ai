# Plan 003: Railway Postgres, API-issued sessions, bucket audio

Workflow phases 0 to 5. Status: complete (item 5.2 handed to plan 007 on 2026-09-25). Date: 2026-09-17.

Scope, decided by the owner on 2026-09-17 (DECISIONS.md D33): the database moves from Supabase to a Postgres service in the Railway project, learner identity is an anonymous session token issued by the API, and rendered audio lives in a Railway bucket served through the API. Supabase leaves the stack. Account linking (email, Google) is deferred to a later auth provider decision.

## Phase 0: Setup

### Analysis

What actually depended on Supabase: Postgres with pgvector (Railway has it), Row Level Security (unused, the browser never queries tables), anonymous auth (replaceable with a small endpoint because the API already verifies JWTs itself), and Storage (Railway buckets are S3-compatible, and the API already serves audio).

The token verifier already accepts HS256 with a shared secret and asymmetric JWKS. The API becomes the HS256 issuer with its own secret; a future provider plugs into the JWKS path. Tokens are long-lived because anonymous learners have no way to sign back in; the web app keeps the token in localStorage and asks for a new one when it is missing or expired.

Audio URLs stay on the API (`/audio/{key}`) regardless of store, so switching stores never rewrites seeded URLs and the bucket needs no public access.

### Behaviors

Sessions:
- Given no token, when POST /session/anonymous is called, then 201 with access_token, user_id, expires_at, and a users row exists with defaults.
- Given the returned token, when GET /me is called with it, then 200 for the same user id.
- Given two calls, then two different users.
- Given a token signed with another secret, then 401.
- Given a token past expiry, then 401.
- Given the session secret is unset outside test, then the API refuses to start issuing (clear error).

Audio:
- Given a key in the store, when GET /audio/{key} is called, then 200 with the right content type and cache headers; unknown key 404; no auth required.
- Given AUDIO_STORE=s3, when put and exists are called, then the S3 client receives put_object and head_object on the configured bucket (stubbed).
- Given the seed with a store, then audio_url is the API's /audio/{key} for every rendered line.

Web:
- Given no stored token, when the client needs a token, then it POSTs /session/anonymous once, stores the token, and reuses it.
- Given an expired stored token, then it requests a new one.
- Given mock mode, then no request is made.

### Phases of work

1. API sessions: settings, issuer, endpoint, verifier wiring, tests.
2. Audio: store protocol gains get, S3 store, /audio route replaces the static mount, seed URLs.
3. Web: session bootstrap without Supabase, dependency removed.
4. Docs: D33, SPEC interfaces, architecture, env examples, READMEs, AGENTS, tech debt 1 and 2 closed.
5. Railway: Dockerfile and railway.toml for the API, deploy notes. Provisioning itself waits for the owner.

### Dependencies

1 before 3. 2 is independent. 4 after 1 to 3. 5 independent.

## Phase 1: Document

Tech debt: the RLS migration becomes a permanent no-op (no auth schema anywhere now); remove it in a later cleanup migration. Long-lived anonymous tokens cannot be revoked individually; rotating SESSION_JWT_SECRET revokes all.

Rollback: git revert. Settings keep SUPABASE_JWT_SECRET readable for one release so a rollback to Supabase-issued tokens is an env change.

## Phase 2: TDD plan

API: unit tests for the issuer (claims, expiry, secret), integration for the endpoint and the audio route, stubbed S3 for the store. Web: session module tests with a mocked fetch and localStorage.

### Checklist

- [x] 1.1 SESSION_JWT_SECRET setting, AUTH_JWKS_URL optional
- [x] 1.2 issue_anonymous_token, POST /session/anonymous
- [x] 1.3 Verifier reads the session secret; JWKS path kept
- [x] 2.1 AudioStore.get, S3AudioStore with boto3
- [x] 2.2 GET /audio/{key} route, static mount removed
- [x] 2.3 Seed emits API audio URLs (unchanged: URLs were already the API's)
- [x] 3.1 Web session bootstrap via /session/anonymous, Supabase client removed
- [x] 4.1 D33, SPEC, architecture, env examples, READMEs, AGENTS, tech debt
- [x] 5.1 Dockerfile, railway.toml, .dockerignore, docs/deploy.md
- [~] 5.2 Provision the Railway project (owner: it creates billable services). Handed to docs/plans/007-deploy.md, which also corrects this plan's deploy files: the image is built from the repo root, migrations run in Railway's pre-deploy step, railway.toml is removed, and Postgres comes from the pgvector template.

## Phase 3 record

Red before green for the session issuer, the session endpoint, the S3 store (botocore stubs), the audio route, and the web session module. Results: API 125 tests at 87.2 percent, web 47 tests at 90 percent, Playwright 3 passed, ruff, mypy strict, eslint, and tsc clean.

Not proved without a Railway project: the S3 adapter against a real bucket, and the Dockerfile build on Railway's builder. The adapter is exercised with botocore stubs and the Dockerfile follows the uv image recipe.

## Phase 4: Review

Feature flag: AUDIO_STORE and the session secret are env-driven; nothing changes for a keyless checkout. Knowledge share: docs/deploy.md is the runbook. Open for the owner: create the Railway project (Postgres, bucket, API service), set the variables from docs/deploy.md, and add the Vercel project.

## Phase 5: Retrospective

What worked: the token verifier abstraction from plan 001 absorbed the auth change with a three-line edit, and keeping audio URLs on the API meant the store swap touched no seeded data.

What did not: Python's mimetypes reports .wav as audio/x-wav, which broke two tests until content types were made explicit. The gh active account flipped between pushes; the switch-push-switch routine is now in memory.

Change for next time: provision infrastructure with the owner in the loop before writing the deploy doc, so the doc records real variable names rather than the documented ones.
