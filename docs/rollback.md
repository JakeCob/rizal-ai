# Rollback

How to undo each kind of change. Updated per plan.

## Code

Every plan lands as one or more commits on main. Rollback is git revert of those commits. Vercel and Railway redeploy from main automatically, so a revert is a deploy.

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

Never run downgrade base against Supabase once learners exist. Write a forward migration instead.

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
