"""add created_at to researches

Revision ID: b6f2e0a7d481
Revises: d4e8a2f5c913
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6f2e0a7d481"
down_revision: Union[str, Sequence[str], None] = "d4e8a2f5c913"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "researches",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # Only needed to backfill existing rows; new inserts always set it via the ORM default.
    op.alter_column("researches", "created_at", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("researches", "created_at")
