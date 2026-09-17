# RizalAI API on Railway. Build context is apps/api (railway.toml sets it).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first so the layer caches across code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# Content is seeded by `rizalai seed` after the first deploy; the YAML is
# copied so the command works inside the container.
ENV CONTENT_DIR=/app/content
ENV PORT=8000
EXPOSE 8000

# Migrations run before the server on every deploy (DECISIONS.md D24).
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn rizalai.main:app --host 0.0.0.0 --port ${PORT}"]
