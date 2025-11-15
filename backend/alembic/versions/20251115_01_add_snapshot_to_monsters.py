"""Add snapshot_data column to monsters."""
from alembic import op
import sqlalchemy as sa


revision = "20251115_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monsters",
        sa.Column("snapshot_data", sa.Text(), nullable=True),
    )
    op.add_column(
        "battle_sessions",
        sa.Column("summary", sa.JSON(), nullable=True),
    )
    op.add_column(
        "battle_sessions",
        sa.Column("combatants", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("battle_sessions", "combatants")
    op.drop_column("battle_sessions", "summary")
    op.drop_column("monsters", "snapshot_data")
