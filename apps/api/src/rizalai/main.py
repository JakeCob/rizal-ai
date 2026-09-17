"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.config import get_settings
from rizalai.db.session import dispose_engine, get_session
from rizalai.generation.router import router as reflection_router
from rizalai.lessons.router import router as lessons_router
from rizalai.progress.review import router as review_router
from rizalai.progress.router import router as progress_router
from rizalai.users.router import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(title="RizalAI API", version="0.1.0", lifespan=lifespan)

    @app.get("/health", tags=["ops"])
    async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
        await session.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}

    app.include_router(users_router)
    app.include_router(lessons_router)
    app.include_router(progress_router)
    app.include_router(review_router)
    app.include_router(reflection_router)

    settings = get_settings()
    if settings.audio_store == "local":
        settings.audio_local_dir.mkdir(parents=True, exist_ok=True)
        app.mount("/audio", StaticFiles(directory=str(settings.audio_local_dir)), name="audio")
    return app


app = create_app()
