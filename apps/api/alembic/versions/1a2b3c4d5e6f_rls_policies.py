"""Row Level Security for learner-owned tables.

The API connects with the service role and scopes every query in code
(DECISIONS.md D22). These policies protect against direct access through the
browser's Supabase client, which only ever needs auth and Storage.

On a local Postgres there is no auth schema, so this migration is a no-op
there. See docs/tech-debt.md item 2.

Revision ID: 1a2b3c4d5e6f
Revises: 05bf904f17e8
Create Date: 2026-09-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "1a2b3c4d5e6f"
down_revision: str | Sequence[str] | None = "05bf904f17e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEARNER_TABLES = ["users", "exercise_attempts", "user_progress", "review_queue"]
CONTENT_TABLES = ["units", "lessons", "exercises", "source_passages"]

GUARD = "SELECT 1 FROM pg_namespace WHERE nspname = 'auth'"


def _owner_column(table: str) -> str:
    return "id" if table == "users" else "user_id"


def upgrade() -> None:
    statements: list[str] = []
    for table in LEARNER_TABLES:
        col = _owner_column(table)
        statements += [
            f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
            f"CREATE POLICY {table}_owner_select ON {table} FOR SELECT USING (auth.uid() = {col})",
        ]
    for table in CONTENT_TABLES:
        statements += [
            f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
            f"CREATE POLICY {table}_read_all ON {table} FOR SELECT USING (true)",
        ]
    body = "; ".join(statements)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS ({GUARD}) THEN
                EXECUTE '{body}';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    statements: list[str] = []
    for table in LEARNER_TABLES:
        statements += [
            f"DROP POLICY IF EXISTS {table}_owner_select ON {table}",
            f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY",
        ]
    for table in CONTENT_TABLES:
        statements += [
            f"DROP POLICY IF EXISTS {table}_read_all ON {table}",
            f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY",
        ]
    body = "; ".join(statements)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS ({GUARD}) THEN
                EXECUTE '{body}';
            END IF;
        END
        $$;
        """
    )
