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
| 8 | The hosted bge-m3 endpoint returns dense vectors only, so sparse is null for real embeddings. Hybrid retrieval falls back to Postgres full-text search until sparse weights are produced by a local bge-m3 run at ingest time. | Plan 001 | Retrieval for extras is built. Either run FlagEmbedding locally in the ingest script or add a tsvector column. |
| 9 | Trailing matter after the last chapter heading (epilogue, glossary, notes) is attached to the last chapter, and footnote paragraphs are kept with kind = footnote rather than excluded. | Plan 001 | Add per-edition terminator patterns when the retriever starts surfacing glossary entries. |
| 10 | Chapter counts differ per edition (the Spanish and English have 64, Poblete's Tagalog has 60 headings). Alignment must be by content, never by chapter number alone. | Plan 001 | Before automated alignment (D19). |
| 11 | The judge score is always null. The reflection publishes on citation validity alone until the threshold is set from the first ten hand-reviewed generations (D21). | Plan 002 | After ANTHROPIC_API_KEY exists and ten reflections have been read. |
| 12 | Repeat completions of the same lesson award full XP each time, provided new attempts exist. There is no reduced practice XP. | Plan 002 | When leagues or leaderboards make XP farming matter. |
| 13 | The practice session refills hearts every ten answers counted over a 30 minute window, and the practice page grades on the server per answer. Offline or slow networks make practice feel slower than lessons. | Plan 002 | If practice latency shows up in the Playwright timing or in use. |
| 14 | XTTS has no Tagalog in its language list; the adapter runs it as English so the bake-off can include it. MMS-TTS needs torch and transformers, which are not project dependencies; install them by hand for the bake-off. | Plan 002 | Resolved by the bake-off decision. Remove the losing adapters. |
