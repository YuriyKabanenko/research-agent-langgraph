"""create users, agents, agent_configs

Revision ID: f3a1c9d2e8b4
Revises:
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a1c9d2e8b4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agent_configs",
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        # sa.Enum(ResearchMode) stores the member *names* ("quick"/"thorough"),
        # not their .value - relevant here since ResearchMode's values are
        # accidentally 1-tuples (trailing commas in state.py), which would be a
        # problem if this stored .value instead.
        sa.Column(
            "research_mode",
            sa.Enum("quick", "thorough", name="researchmode"),
            nullable=False,
        ),
        sa.Column("retry_max_count", sa.Integer(), nullable=False),
        sa.Column("critique_threshold", sa.Integer(), nullable=False),
        sa.Column("api_token", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("agent_id"),
    )


def downgrade() -> None:
    op.drop_table("agent_configs")
    op.drop_table("agents")
    op.drop_table("users")
    # CREATE TYPE happens implicitly as part of the create_table above, but
    # DROP TABLE never drops the enum type it used - Postgres leaves it in the
    # catalog, so a re-run of upgrade() would fail on "type already exists"
    # unless it's dropped explicitly here.
    sa.Enum(name="researchmode").drop(op.get_bind(), checkfirst=False)
