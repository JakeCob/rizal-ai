# RizalAI API image (DECISIONS.md D37).
#
# Build context is the REPO ROOT, so content/ can be baked into the image:
#   docker build -f apps/api/Dockerfile -t rizalai-api .
#
# Railway service settings (set in the dashboard; railway.toml is gone):
#   Root directory:        empty (repo root)
#   RAILWAY_DOCKERFILE_PATH=/apps/api/Dockerfile   (service variable)
#   Watch paths:           /apps/api/** and /content/**
#   Pre-deploy command:    alembic upgrade head    (a failed migration blocks the deploy)
#   Start command:         none (this CMD)
#   Healthcheck path:      /health
#   Restart policy:        on failure
# Variables: ENV=production (Railway's injected RAILWAY_ENVIRONMENT also
# means production when ENV is unset; any other ENV there refuses to start).
# In production the API refuses to start, naming the variable, when any of
# SESSION_JWT_SECRET, CORS_ORIGINS, DATABASE_URL or LLM_PROVIDER is unset or
# still a local default, and under AUDIO_STORE=s3 when an S3 setting or
# AUDIO_BASE_URL is. See docs/deploy.md section 2.
# The private database domain resolves only at runtime and in pre-deploy,
# never during the build, so nothing here touches the database.

ARG PYTHON_IMAGE=python:3.12-slim-bookworm

FROM ${PYTHON_IMAGE} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# uv pinned to the version uv.lock and the uv_build backend expect.
COPY --from=ghcr.io/astral-sh/uv:0.11.24 /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first so this layer caches across code changes.
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then the project itself, installed non-editable into the venv.
COPY apps/api/README.md ./
COPY apps/api/src ./src
RUN uv sync --frozen --no-dev --no-editable



FROM ${PYTHON_IMAGE} AS runtime

# FORWARDED_ALLOW_IPS=* trusts X-Forwarded-* from any peer: Railway's edge
# proxy is the only one. Revisit if rate limiting or IP logging ever reads the
# client address.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH \
    CONTENT_DIR=/app/content \
    FORWARDED_ALLOW_IPS=*

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app --no-create-home app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app apps/api/alembic.ini ./alembic.ini
COPY --chown=app:app apps/api/alembic ./alembic
COPY --chown=app:app content ./content
RUN mkdir -p /app/data/raw /app/data/audio && chown -R app:app /app/data
# The pinned Gutenberg texts (D37). A plain COPY, so a missing text fails the
# build instead of shipping an empty corpus directory.
COPY --chown=app:app apps/api/data/raw/ /app/data/raw/

USER app
EXPOSE 8000

# Migrations run in Railway's pre-deploy step, not here, so a failed
# migration blocks the deploy instead of crash-looping every replica.
CMD ["sh", "-c", "exec uvicorn rizalai.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
