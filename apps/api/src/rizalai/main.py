"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.db.session import dispose_engine, get_session
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
    return app


app = create_app()
