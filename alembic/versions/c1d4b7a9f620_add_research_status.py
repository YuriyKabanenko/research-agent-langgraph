"""add research status

Revision ID: c1d4b7a9f620
Revises: 8f793094c151
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d4b7a9f620"
down_revision: Union[str, Sequence[str], None] = "8f793094c151"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

research_status = sa.Enum(
    "pending", "running", "completed", "failed", name="researchstatus"
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    # ADD COLUMN doesn't fire the "before create table" event that would
    # otherwise emit CREATE TYPE for us, so it has to happen explicitly here.
    research_status.create(bind, checkfirst=True)
    op.add_column(
        "researches",
        sa.Column(
            "status",
            research_status,
            nullable=False,
            server_default="pending",
        ),
    )
    # Only needed to backfill existing rows; new inserts always set status explicitly.
    op.alter_column("researches", "status", server_default=None)
    op.add_column("researches", sa.Column("error_message", sa.String(), nullable=True))
    # The research result is now written by a background task after the row
    # is created, so it doesn't exist yet at insert time.
    op.alter_column("researches", "resarch", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("researches", "resarch", existing_type=sa.String(), nullable=False)
    op.drop_column("researches", "error_message")
    op.drop_column("researches", "status")
    # DROP TABLE doesn't drop the enum type it used - see f3a1c9d2e8b4 for the
    # same gotcha with researchmode.
    research_status.drop(bind=op.get_bind(), checkfirst=False)
