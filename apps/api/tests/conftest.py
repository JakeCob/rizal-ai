"""Shared fixtures.

Integration tests run against TEST_DATABASE_URL (rizalai_test locally, a
service container in CI). The schema is created once per session by running
the real Alembic migrations, so migrations are exercised on every test run.
Each test gets a connection with an outer transaction that is rolled back at
the end, so tests never see each other's rows.
"""

import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

os.environ["ENV"] = "test"
os.environ["SESSION_JWT_SECRET"] = "test-secret-do-not-use-in-production"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from rizalai.config import get_settings
from rizalai.db.session import get_session

API_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def migrated_schema() -> None:
    env = {**os.environ, "ENV": "test"}
    subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=API_ROOT, env=env, check=True
    )


@pytest.fixture(scope="session")
async def engine(migrated_schema: None) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(get_settings().active_database_url)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        trans = await conn.begin()
        factory = async_sessionmaker(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with factory() as session:
            yield session
        await trans.rollback()


@pytest.fixture
async def client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    from rizalai.main import app

    async def _override() -> AsyncIterator[AsyncSession]:
        yield db

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
