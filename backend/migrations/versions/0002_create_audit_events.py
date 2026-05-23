"""Create append-only audit events table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the audit table and grant append/read access to the audit role."""
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("query_id", sa.String(length=80), nullable=False, unique=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_audit_events_query_id", "audit_events", ["query_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])
    _grant_audit_role_permissions()


def downgrade() -> None:
    """Drop the audit table."""
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_query_id", table_name="audit_events")
    op.drop_table("audit_events")


def _grant_audit_role_permissions() -> None:
    """Grant local audit role append-only table access."""
    op.execute(
        """
        DO
        $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vellum_auditor') THEN
                GRANT USAGE ON SCHEMA public TO vellum_auditor;
                GRANT SELECT, INSERT ON TABLE audit_events TO vellum_auditor;
            END IF;
        END
        $$;
        """
    )
