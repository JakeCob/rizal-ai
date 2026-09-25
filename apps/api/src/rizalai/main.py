"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.audio.routes import router as audio_router
from rizalai.auth.session import router as session_router
from rizalai.config import get_settings
from rizalai.db.session import dispose_engine, get_session
from rizalai.generation.router import router as reflection_router
from rizalai.lessons.router import router as lessons_router
from rizalai.logging_setup import configure_logging
from rizalai.progress.review import router as review_router
from rizalai.progress.router import router as progress_router
from rizalai.users.router import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(title="RizalAI API", version="0.1.0", lifespan=lifespan)
    settings = get_settings()
    settings.validate_for_production()
    configure_logging(settings.log_level)
    # The web app calls the API cross-origin with a bearer token (D36).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Timezone"],
    )

    @app.get("/health", tags=["ops"])
    async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
        await session.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}

    app.include_router(users_router)
    app.include_router(lessons_router)
    app.include_router(progress_router)
    app.include_router(review_router)
    app.include_router(reflection_router)
    app.include_router(session_router)
    app.include_router(audio_router)
    return app


app = create_app()
