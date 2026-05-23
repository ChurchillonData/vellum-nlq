from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID


metadata = MetaData()

plans = Table(
    "plans",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("plan_code", String(40), nullable=False, unique=True),
    Column("plan_tier", String(80), nullable=False),
    Column("hospital_network", String(80), nullable=False),
    Column("excess_amount", Numeric(12, 2), nullable=False),
)

members = Table(
    "members",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("plan_id", UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False),
    Column("region", String(80), nullable=False),
    Column("date_of_birth", Date, nullable=False),
    Column("enrolled_from", Date, nullable=False),
    Column("enrolled_to", Date),
)

providers = Table(
    "providers",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("name", String(160), nullable=False),
    Column("specialty", String(120), nullable=False),
    Column("network_status", String(40), nullable=False),
    Column("region", String(80), nullable=False),
)

enrolment_months = Table(
    "enrolment_months",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("member_id", UUID(as_uuid=True), ForeignKey("members.id"), nullable=False),
    Column("coverage_month", Date, nullable=False),
    Column("member_months", Numeric(8, 2), nullable=False),
)

claims = Table(
    "claims",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("member_id", UUID(as_uuid=True), ForeignKey("members.id"), nullable=False),
    Column("incurred_date", Date, nullable=False),
    Column("received_date", Date, nullable=False),
    Column("adjudicated_date", Date),
    Column("closed_date", Date),
    Column("status", String(40), nullable=False),
    Column("net_incurred_amount", Numeric(12, 2), nullable=False),
    CheckConstraint("net_incurred_amount >= 0", name="ck_claims_net_incurred_non_negative"),
)

claim_lines = Table(
    "claim_lines",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("claim_id", UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False),
    Column("provider_id", UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False),
    Column("service_date", Date, nullable=False),
    Column("procedure_code", String(40), nullable=False),
    Column("diagnosis_category", String(120), nullable=False),
    Column("paid_date", Date),
    Column("net_paid_amount", Numeric(12, 2), nullable=False),
    Column("declined_amount", Numeric(12, 2), nullable=False),
)

claim_status_history = Table(
    "claim_status_history",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("claim_id", UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False),
    Column("status", String(40), nullable=False),
    Column("changed_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

reserves = Table(
    "reserves",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("claim_id", UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False),
    Column("snapshot_date", Date, nullable=False),
    Column("case_reserve_amount", Numeric(12, 2), nullable=False),
)

premium = Table(
    "premium",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("member_id", UUID(as_uuid=True), ForeignKey("members.id"), nullable=False),
    Column("coverage_month", Date, nullable=False),
    Column("earned_amount", Numeric(12, 2), nullable=False),
)

declines = Table(
    "declines",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("claim_line_id", UUID(as_uuid=True), ForeignKey("claim_lines.id"), nullable=False),
    Column("reason_code", String(80), nullable=False),
    Column("reason_text", Text, nullable=False),
)

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("query_id", String(80), nullable=False, unique=True),
    Column("event_type", String(80), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSONB, nullable=False),
)
