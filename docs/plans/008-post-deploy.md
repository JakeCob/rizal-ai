# Plan 008: Post-deploy chores

Workflow phases 0 to 5. Status: complete. Date: 2026-09-25. Same setup as plan 007 (builder, reviewer, architect as tester). Deploys automatically to Railway on merge (D37).

Scope, chosen by the owner on 2026-09-25 while the Vercel project is set up: the small debts the first production deploy made due. Tech debt 16 (remove the SUPABASE_JWT_SECRET fallback and the stale Supabase wording), tech debt 2 (a cleanup migration for the RLS policies now that a production database exists), tech debt 29 (application logging so INFO from rizalai reaches Railway logs), and the missing test for the bootstrap guard's exercise-only deletion path (plan 007 re-check).

## Phase 0: Setup

### Analysis

- Tech debt 16: `supabase_jwt_secret` in config.py is read as a fallback in auth/deps.py (`settings.session_jwt_secret or settings.supabase_jwt_secret`). Production issues and verifies tokens with SESSION_JWT_SECRET only. Stale wording remains in auth/__init__.py, auth/jwt.py, tests/helpers.py, tests/unit/test_jwt_verify.py, alembic/env.py and db/models.py (a comment on a closed debt).
- Tech debt 2: migration 1a2b3c4d5e6f created RLS policies only when an auth schema existed; no database ever had one, so it is a permanent no-op. History stays untouched (D24: migrations are forward-only). A forward migration makes the state explicit and idempotent: drop the named policies if they exist and disable RLS on the eight learner tables where it is enabled, with a downgrade that is a no-op.
- Tech debt 29: the app configures no logging; under uvicorn only WARNING and above reach stderr. A LOG_LEVEL setting (default INFO) applied at app creation with a plain formatter that includes the logger name gives Railway logs the reflection fallbacks and the like.
- Guard test: plan 007's re-check found no test for the case where an exercise key is renamed inside a lesson that stays; the guard must refuse when attempts or review rows reference the removed exercise.

### Behaviors

- Given SESSION_JWT_SECRET unset and SUPABASE_JWT_SECRET set, when the API verifies a bearer token, then verification fails (the fallback is gone) and the setting no longer exists on Settings.
- Given a database where the RLS migration ran, when the cleanup migration runs, then no policy named *_owner_select or *_read_all exists and RLS is disabled on the eight tables; running it again changes nothing; downgrade is a no-op.
- Given LOG_LEVEL unset, when the app is created, then rizalai loggers emit INFO and above with the logger name; LOG_LEVEL=WARNING silences INFO.
- Given a completed lesson whose exercise key is renamed in content, when bootstrap runs, then it refuses naming the exercise and the attempt and review row counts, and proceeds with --allow-learner-data-loss.

### File ownership

| Worker | Files |
|---|---|
| builder | apps/api/src/rizalai/config.py, auth/deps.py, auth/__init__.py, auth/jwt.py, main.py (logging), a new alembic migration, db/models.py (comment), alembic/env.py (comment), tests/helpers.py, tests/unit/test_jwt_verify.py, tests/unit/test_config.py, tests/integration/test_rls_cleanup.py (new), tests/unit/test_logging.py (new), tests/integration/test_bootstrap.py (one test), .env.example files (SUPABASE_JWT_SECRET removed, LOG_LEVEL added) |
| reviewer | reads everything, edits nothing |
| architect | this plan, docs/tech-debt.md, docs/deploy.md (LOG_LEVEL) |

## Phase 1: Document

Tech debt: closes 16, 2 and 29. Rollback: revert the commit; the cleanup migration's downgrade is a no-op by design, so a revert of code alone leaves the database in the cleaned state, which is also the state every database was effectively in.

## Phase 2: TDD plan

Red first per item: a test that SUPABASE_JWT_SECRET no longer works as a fallback; a migration test on rizalai_test that inspects pg_policies and relrowsecurity after upgrade head; a logging test that captures a rizalai INFO record through the configured handler; the guard test. Then green, ruff, mypy, full suite.

### Checklist

- [x] A. Supabase fallback and wording removed: builder, reviewer
- [x] B. RLS cleanup migration: builder, reviewer
- [x] C. Application logging with LOG_LEVEL: builder, reviewer
- [x] D. Bootstrap guard test for exercise-only deletion: builder, reviewer
- [x] E. Architect: suite, migration cycle on the dev database, docs, commit, push; confirm the Railway deploy runs the new migration in pre-deploy and the logs show INFO lines

## Phase 3 record

One builder brief, one review, MERGE on first pass with two logging nits. Red shown per task: the Supabase setting and fallback tests fail on the previous code; the RLS test builds a policy and enabled RLS then runs the cleanup migration's upgrade and asserts the state; the logging tests fail without the handler; the guard test for a renamed exercise key passed on its first run because plan 007's guard already counted exercise rows, so it pins that behavior. The migration was written with a generated id rather than `alembic revision`, so a concurrent suite run could not stamp an empty stub (plan 005's race). Architect: 296 passed, 89.6 percent coverage, ruff and mypy clean; migration 863927f6ead6 cycled up, down and up on the dev database; no policies remain.

## Phase 4: Review

- One commit for the code and one for the docs; pushed; Railway deploys it from main and runs the cleanup migration in pre-deploy.
- Docs: tech debt rows 2, 16 and 29 removed; docs/deploy.md gains LOG_LEVEL and loses SUPABASE_JWT_SECRET; the .env.example files follow.
- Feature flag: none. LOG_LEVEL defaults to INFO.

## Phase 5: Retrospective

A one-brief plan for small debts works when each item has a clear red test; the review had nothing to fix. Writing migration files with a generated id avoids the stub race for good. Next: the audio bake-off (tech debt 14) once the owner can listen on the phone, and Unit 3 content.
