# contracts

The API contract as one JSON Schema document, generated from the Pydantic models in `apps/api/src/rizalai/contracts/`. The web app generates its TypeScript types from it, so the two sides cannot drift.

Regenerate after any contract change:

```
cd apps/api && uv run rizalai export-contracts ../../packages/contracts/schema.json
cd apps/web && pnpm gen:types
```

`schema.json` is committed. A CI check regenerates it and fails on a diff.

Top-level types: `LessonOut`, `Tree`, `UserOut`, and the four exercise variants `SentenceAssembly`, `TranslateLine`, `ListenTap`, `ComprehensionMC`.
