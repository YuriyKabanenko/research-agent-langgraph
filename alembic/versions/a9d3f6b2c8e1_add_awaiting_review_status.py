"""add awaiting_review research status

Revision ID: a9d3f6b2c8e1
Revises: f18a6c2b7e05
Create Date: 2026-09-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a9d3f6b2c8e1"
down_revision: Union[str, Sequence[str], None] = "f18a6c2b7e05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Hand-written: autogenerate doesn't detect new values on an existing enum type.
    # Set while the graph is paused in human_review, waiting for the user's decision.
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'awaiting_review'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres can't drop a value from an enum type (short of recreating the type and
    # rewriting every column using it), so the value is left in place.
    pass
