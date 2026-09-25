"""drop unit published

Units carry no published flag (DECISIONS.md D35): the column was seeded and
never read, and lessons lock themselves through lessons.published. The
downgrade restores the column as NOT NULL with a server default of true.

Revision ID: 40506cb22e4f
Revises: 2b9cbe200329
Create Date: 2026-09-25 07:38:05.733056

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "40506cb22e4f"
down_revision: str | Sequence[str] | None = "2b9cbe200329"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("units", "published")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("units", sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.true()))
