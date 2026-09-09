"""add agent_id to researches

Revision ID: d4e8a2f5c913
Revises: c1d4b7a9f620
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e8a2f5c913"
down_revision: Union[str, Sequence[str], None] = "c1d4b7a9f620"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # nullable=False with no backfill default - fine while the table is still
    # empty in every environment this has run against. If that's no longer
    # true, this needs a backfill step before tightening the constraint.
    op.add_column("researches", sa.Column("agent_id", sa.Uuid(), nullable=False))
    op.create_foreign_key(
        "fk_researches_agent_id_agents", "researches", "agents", ["agent_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_researches_agent_id_agents", "researches", type_="foreignkey")
    op.drop_column("researches", "agent_id")
