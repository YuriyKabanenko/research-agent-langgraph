"""add web_search_enabled and tavily_api_token to agent_configs

Revision ID: b3e9c4d7a215
Revises: a9d3f6b2c8e1
Create Date: 2026-09-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3e9c4d7a215"
down_revision: Union[str, Sequence[str], None] = "a9d3f6b2c8e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default backfills existing configs as "web search off" - they have no
    # Tavily key of their own, and falling back to the operator's is exactly what this
    # feature exists to prevent.
    op.add_column(
        "agent_configs",
        sa.Column("web_search_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("agent_configs", sa.Column("tavily_api_token", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("agent_configs", "tavily_api_token")
    op.drop_column("agent_configs", "web_search_enabled")
