"""Ensure battle_sessions summary/combatants columns exist."""
from alembic import op
import sqlalchemy as sa


revision = "20251116_03"
down_revision = "20251116_02"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns(table)]
    return column in columns


def upgrade() -> None:
    if not _has_column("battle_sessions", "summary"):
        op.add_column(
            "battle_sessions",
            sa.Column("summary", sa.JSON(), nullable=True),
        )
    if not _has_column("battle_sessions", "combatants"):
        op.add_column(
            "battle_sessions",
            sa.Column("combatants", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("battle_sessions", "combatants"):
        op.drop_column("battle_sessions", "combatants")
    if _has_column("battle_sessions", "summary"):
        op.drop_column("battle_sessions", "summary")
