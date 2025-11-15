"""Convert skill history column to JSON."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20251116_02"
down_revision = "20251116_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "skill_cards",
        "history",
        type_=sa.JSON(),
        postgresql_using="to_json(history)",
    )


def downgrade() -> None:
    op.alter_column(
        "skill_cards",
        "history",
        type_=postgresql.ARRAY(sa.Text()),
        postgresql_using="ARRAY(SELECT json_array_elements_text(history))",
    )
