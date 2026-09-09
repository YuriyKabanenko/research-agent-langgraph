"""add tools_used and research_rate to researches

Revision ID: f18a6c2b7e05
Revises: e2b7d5a1f934
Create Date: 2026-09-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = "f18a6c2b7e05"
down_revision: Union[str, Sequence[str], None] = "e2b7d5a1f934"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Nullable - only populated once the background research task completes,
    # same as the existing resarch/error_message columns.
    op.add_column("researches", sa.Column("tools_used", ARRAY(sa.String()), nullable=True))
    op.add_column("researches", sa.Column("research_rate", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("researches", "research_rate")
    op.drop_column("researches", "tools_used")
