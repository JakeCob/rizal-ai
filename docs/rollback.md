# Rollback

How to undo each kind of change. Updated per plan.

## Code

Every plan lands as one or more commits on main. Rollback is git revert of those commits. Vercel and Railway redeploy from main automatically, so a revert is a deploy.

A blocked browser request after a deploy (a CORS error in the console) is usually configuration, not code: fix CORS_ORIGINS or CORS_ORIGIN_REGEX on the Railway service and redeploy (D36). A CORS error on one endpoint while the others work usually means that endpoint returned an unhandled 500 (Starlette's error middleware sits outside CORS, so the error response carries no allow-origin header): read the API logs before touching the origin settings.

A revert that touches apps/api/src/rizalai/contracts must also revert packages/contracts/schema.json and apps/web/lib/types.generated.ts, or CI fails on drift. Reverting the whole commit does this; a partial revert must re-run export-contracts and gen:types.

## Database schema

Alembic owns the schema. Each migration has a downgrade. To roll back one migration:

```
cd apps/api
uv run alembic downgrade -1
```

To wipe a local or test database:

```
uv run alembic downgrade base
```

Never run downgrade base against the Railway database once learners exist. Write a forward migration instead. A downgrade that restores a dropped column must give it a server default so existing rows stay valid (the units.published downgrade in plan 005 does).

## Content

Content is seeded from YAML. Re-seeding after a git revert of the content file restores the previous lesson_version. Progress rows record the lesson_version they were completed against, so a revert does not orphan them.

## Corpus

Ingest is idempotent. To remove one work:

```
DELETE FROM source_passages WHERE work = 'noli';
```

Re-run the ingest script to restore it.

## Generated content

Reflection cache rows are keyed by lesson version, prompt version, and model. Bumping prompt_version invalidates every cached reflection at once. Rejecting one row through the CLI invalidates only that lesson.
