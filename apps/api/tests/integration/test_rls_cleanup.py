"""Behaviors for the RLS cleanup migration (plan 008, tech debt 2):
- Given the test database at head, then no policy named *_owner_select or
  *_read_all exists and RLS is off on the eight tables 1a2b3c4d5e6f named.
- Given a database where those policies exist and RLS is on (created here
  inside the test's rolled-back transaction, with USING (true) because no
  auth schema exists), when the cleanup migration's upgrade() runs, then the
  policies are gone and RLS is off; a second run changes nothing; and
  downgrade() is a no-op.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text

from rizalai.ops.bootstrap import script_head

pytestmark = pytest.mark.anyio

API_ROOT = Path(__file__).resolve().parents[2]
VERSIONS = API_ROOT / "alembic" / "versions"
LEARNER_TABLES = ["users", "exercise_attempts", "user_progress", "review_queue"]
CONTENT_TABLES = ["units", "lessons", "exercises", "source_passages"]
TABLES = LEARNER_TABLES + CONTENT_TABLES
POLICIES = [(t, f"{t}_owner_select") for t in LEARNER_TABLES] + [(t, f"{t}_read_all") for t in CONTENT_TABLES]


def _migration() -> ModuleType:
    [path] = VERSIONS.glob("*_drop_rls_policies.py")
    spec = importlib.util.spec_from_file_location("drop_rls_policies", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _state(conn) -> tuple[list[str], list[str]]:
    policies = (
        (
            await conn.execute(
                text(
                    "select policyname from pg_policies where schemaname = 'public' and "
                    "(policyname like '%\\_owner\\_select' or policyname like '%\\_read\\_all') "
                    "order by 1"
                )
            )
        )
        .scalars()
        .all()
    )
    secured = (
        (
            await conn.execute(
                text(
                    "select relname from pg_class where relname = any(:tables) and relrowsecurity order by 1"
                ),
                {"tables": TABLES},
            )
        )
        .scalars()
        .all()
    )
    return list(policies), list(secured)


def _run(sync_conn, module: ModuleType, step: str) -> None:
    with Operations.context(MigrationContext.configure(sync_conn)):
        getattr(module, step)()


async def test_the_cleanup_migration_is_the_head():
    assert _migration().revision == script_head(API_ROOT / "alembic.ini")
    assert _migration().down_revision == "40506cb22e4f"


async def test_head_has_no_rls_left(db):
    conn = await db.connection()
    assert await _state(conn) == ([], [])


async def test_upgrade_drops_policies_and_disables_rls_idempotently(db):
    conn = await db.connection()
    for table, policy in POLICIES:
        await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        await conn.execute(text(f"CREATE POLICY {policy} ON {table} FOR SELECT USING (true)"))
    policies, secured = await _state(conn)
    assert len(policies) == 8 and sorted(secured) == sorted(TABLES)

    module = _migration()
    await conn.run_sync(_run, module, "upgrade")
    assert await _state(conn) == ([], [])

    await conn.run_sync(_run, module, "upgrade")  # idempotent
    assert await _state(conn) == ([], [])


async def test_downgrade_is_a_no_op(db):
    conn = await db.connection()
    await conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY"))
    await conn.run_sync(_run, _migration(), "downgrade")
    assert await _state(conn) == ([], ["users"])  # untouched
