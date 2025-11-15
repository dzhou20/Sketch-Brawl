"""Add demo_artifacts and telemetry_events tables."""
from alembic import op
import sqlalchemy as sa


revision = "20251116_01"
down_revision = "20251115_01"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    created_demo_artifacts = False
    created_telemetry_events = False

    if not _has_table("demo_artifacts"):
        created_demo_artifacts = True
        op.create_table(
            "demo_artifacts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("artifact_type", sa.String(length=64), nullable=False),
            sa.Column("version", sa.String(length=64), nullable=False),
            sa.Column("uri", sa.Text(), nullable=False),
            sa.Column("checksum", sa.String(length=255), nullable=False),
            sa.Column("generated_from_commit", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
    if created_demo_artifacts:
        op.create_index("ix_demo_artifacts_artifact_type", "demo_artifacts", ["artifact_type"])

    if not _has_table("telemetry_events"):
        created_telemetry_events = True
        op.create_table(
            "telemetry_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("session_id", sa.String(length=64), nullable=False),
            sa.Column("source", sa.String(length=64), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("captured_at", sa.DateTime(), nullable=True),
        )
    if created_telemetry_events:
        op.create_index("ix_telemetry_events_session_id", "telemetry_events", ["session_id"])
        op.create_index("ix_telemetry_events_event_type", "telemetry_events", ["event_type"])


def downgrade() -> None:
    if _has_table("telemetry_events"):
        op.drop_index("ix_telemetry_events_event_type", table_name="telemetry_events")
        op.drop_index("ix_telemetry_events_session_id", table_name="telemetry_events")
        op.drop_table("telemetry_events")
    if _has_table("demo_artifacts"):
        op.drop_index("ix_demo_artifacts_artifact_type", table_name="demo_artifacts")
        op.drop_table("demo_artifacts")
