# Tech Debt

Known shortcuts, each with the plan that introduced it and the condition for paying it off. Remove an entry when it is resolved.

| # | Debt | Introduced | Pay off when |
|---|---|---|---|
| 1 | users.id has no foreign key to auth.users, because the local Postgres has no auth schema. | Plan 001 | A Supabase project exists. Add the constraint in a migration guarded on the auth schema. |
| 2 | The RLS policies migration is a no-op when the auth schema is absent, so RLS is untested locally. | Plan 001 | Before first deploy, run the migration against Supabase and add a test that uses the anon key to confirm cross-user reads fail. |
| 3 | The seeded lesson is a labeled placeholder, not authored content. | Plan 001 | Plan 002 replaces it with the Chapter 1 lesson. |
| 4 | Sparse vectors are stored as jsonb with no index. | Plan 001 | Retrieval for extras is built. Add a GIN index or a dedicated sparse index. |
| 5 | Runner completion is not persisted; XP shown at the end of a session is client-side only. | Plan 001 | Plan 002 adds POST /attempts and POST /lessons/{id}/complete. |
| 6 | No audio in the scaffold; audio_url is nullable and the player shows a disabled control. | Plan 001 | Plan 002 renders pre-rendered audio after the TTS bake-off. |
| 7 | Migrations run in tests through a subprocess rather than in-process, because Alembic's async env cannot be called from inside a running event loop. | Plan 001 | Only if test startup time becomes a problem. |
