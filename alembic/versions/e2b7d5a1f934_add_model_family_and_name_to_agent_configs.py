"""add model_family and model_name to agent_configs

Revision ID: e2b7d5a1f934
Revises: b6f2e0a7d481
Create Date: 2026-09-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2b7d5a1f934"
down_revision: Union[str, Sequence[str], None] = "b6f2e0a7d481"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# sa.Enum(ModelFamily) stores the member *names*, matching the researchmode enum
# in f3a1c9d2e8b4.
model_family = sa.Enum("anthropic", "openai", "google", name="modelfamily")


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    model_family.create(bind, checkfirst=True)
    # nullable=False with no backfill default - fine while the table is still
    # empty in every environment this has run against, same as the other
    # agent_configs columns added in f3a1c9d2e8b4.
    op.add_column("agent_configs", sa.Column("model_family", model_family, nullable=False))
    op.add_column("agent_configs", sa.Column("model_name", sa.String(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("agent_configs", "model_name")
    op.drop_column("agent_configs", "model_family")
    # DROP TABLE never drops the enum type it used - see f3a1c9d2e8b4 for the same gotcha.
    model_family.drop(bind=op.get_bind(), checkfirst=False)
