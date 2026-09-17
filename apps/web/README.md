# RizalAI web

Next.js 15 App Router, TypeScript, Tailwind v4, shadcn/ui (Base UI), TanStack Query. Mobile-first: the layout is a phone column at every width. Node 22 and pnpm 9.

## Run

```
cp .env.example .env.local     # mock mode by default
pnpm install
pnpm dev                       # http://localhost:3000
```

Mock mode serves fixtures from `lib/api/fixtures.ts`, so the tree and the lesson play with no backend. To use the real API, clear `NEXT_PUBLIC_API_MODE` and set the Supabase URL and anon key; the first visit signs in anonymously.

## Test

```
pnpm test        # Vitest, jsdom, 80 percent coverage gate on components/ and lib/
pnpm test:e2e    # Playwright, iPhone 13 viewport, plays the lesson end to end in mock mode
pnpm typecheck
pnpm lint
```

## Types from the API

`lib/types.generated.ts` is generated from `packages/contracts/schema.json`. Never edit it. After a contract change on the API side:

```
pnpm gen:types
```

## Layout

```
app/
  layout.tsx           fonts, providers, phone column, service worker
  page.tsx             skill tree
  lesson/[id]/page.tsx runner
components/
  tree/                SkillTree, PathNode
  runner/              Runner (state from lib/runner), VignettePlayer, ExerciseView, TileBank
  ui/                  shadcn components
lib/
  api/                 client (http and mock), fixtures
  auth/                Supabase anonymous session
  runner/              reducer and grading, pure and unit tested
e2e/                   Playwright
public/                manifest, icon, service worker
```

## Frontend decisions, explained

- The runner is a pure reducer in `lib/runner/reducer.ts` and the component only renders state. That is why every exercise transition is local and why the logic is tested without a browser.
- The API client is the only network path. Pages call it through TanStack Query, which handles loading, caching, and retries.
- The answer key ships with the lesson. Grading is local for the 200ms budget; the server re-grades at completion (plan 002).
- shadcn here is the Base UI flavor, so triggers take a `render` prop rather than `asChild`.
