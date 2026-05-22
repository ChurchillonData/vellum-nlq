"""Create the first claims analytics schema."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the tables required by the playbook schema."""
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_code", sa.String(length=40), nullable=False, unique=True),
        sa.Column("plan_tier", sa.String(length=80), nullable=False),
        sa.Column("hospital_network", sa.String(length=80), nullable=False),
        sa.Column("excess_amount", sa.Numeric(12, 2), nullable=False),
    )
    op.create_table(
        "members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("enrolled_from", sa.Date(), nullable=False),
        sa.Column("enrolled_to", sa.Date()),
    )
    op.create_table(
        "providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("specialty", sa.String(length=120), nullable=False),
        sa.Column("network_status", sa.String(length=40), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=False),
    )
    op.create_table(
        "enrolment_months",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("coverage_month", sa.Date(), nullable=False),
        sa.Column("member_months", sa.Numeric(8, 2), nullable=False),
    )
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("incurred_date", sa.Date(), nullable=False),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column("adjudicated_date", sa.Date()),
        sa.Column("closed_date", sa.Date()),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("net_incurred_amount", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("net_incurred_amount >= 0", name="ck_claims_net_incurred_non_negative"),
    )
    op.create_table(
        "claim_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("procedure_code", sa.String(length=40), nullable=False),
        sa.Column("diagnosis_category", sa.String(length=120), nullable=False),
        sa.Column("paid_date", sa.Date()),
        sa.Column("net_paid_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("declined_amount", sa.Numeric(12, 2), nullable=False),
    )
    op.create_table(
        "claim_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "reserves",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("case_reserve_amount", sa.Numeric(12, 2), nullable=False),
    )
    op.create_table(
        "premium",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("coverage_month", sa.Date(), nullable=False),
        sa.Column("earned_amount", sa.Numeric(12, 2), nullable=False),
    )
    op.create_table(
        "declines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_line_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claim_lines.id"), nullable=False),
        sa.Column("reason_code", sa.String(length=80), nullable=False),
        sa.Column("reason_text", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    """Drop the claims analytics tables in dependency order."""
    op.drop_table("declines")
    op.drop_table("premium")
    op.drop_table("reserves")
    op.drop_table("claim_status_history")
    op.drop_table("claim_lines")
    op.drop_table("claims")
    op.drop_table("enrolment_months")
    op.drop_table("providers")
    op.drop_table("members")
    op.drop_table("plans")
