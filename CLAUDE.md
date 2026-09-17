# CLAUDE.md

Project instructions for Claude Code. The full agent guide is in AGENTS.md and is imported below so the two never drift.

@AGENTS.md

## Claude Code specifics

- Prefer the lean-ctx tools for reading and searching when they are available, per the global CLAUDE.md. Native Bash is fine for running tests and git.
- When a decision needs the owner, ask through the question tool with a recommended option first and several independent questions per call. Do not block on questions that a sensible default resolves.
- Memory for this project lives in the Claude memory directory, not in the repo. Repo docs are the source of truth for anything a contributor needs.
