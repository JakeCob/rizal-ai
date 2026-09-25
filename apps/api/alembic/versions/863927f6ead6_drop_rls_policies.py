"""drop rls policies

Tech debt 2. Migration 1a2b3c4d5e6f created Row Level Security policies only
when an auth schema existed, and no database ever had one, so it has always
been a no-op. This migration makes the intended state explicit: the named
policies do not exist and RLS is off on the eight tables. It is idempotent
(DROP POLICY IF EXISTS; disabling RLS that is already off is harmless), so it
is safe on any database, whatever 1a2b3c4d5e6f did there.

Downgrade is a no-op on purpose: migrations are forward-only (DECISIONS.md
D24), and 1a2b3c4d5e6f stays in history as the record of what the policies
were.

Revision ID: 863927f6ead6
Revises: 40506cb22e4f
Create Date: 2026-09-26

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "863927f6ead6"
down_revision: str | Sequence[str] | None = "40506cb22e4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The tables and policy names 1a2b3c4d5e6f used.
LEARNER_TABLES = ["users", "exercise_attempts", "user_progress", "review_queue"]
CONTENT_TABLES = ["units", "lessons", "exercises", "source_passages"]


def upgrade() -> None:
    """Upgrade schema."""
    for table in LEARNER_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_owner_select ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    for table in CONTENT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_read_all ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Downgrade schema: nothing to do (forward-only, D24)."""
