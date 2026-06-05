from dataclasses import dataclass


@dataclass(frozen=True)
class AdditionalMetricDefinition:
    """Implementation metadata for one simple governed aggregate metric."""

    metric_id: str
    required_tables: frozenset[str]
    time_anchor: str
    tables: tuple[str, ...]
    join_pairs: tuple[tuple[str, str], ...]
    extra_filters: tuple[str, ...] = ()


ADDITIONAL_METRICS = {
    definition.metric_id: definition
    for definition in (
        AdditionalMetricDefinition(
            metric_id="claim_count",
            required_tables=frozenset({"claims"}),
            time_anchor="claims.incurred_date",
            tables=("claims", "members", "plans"),
            join_pairs=(("claims", "members"), ("members", "plans")),
            extra_filters=("claims.status != excluded_status",),
        ),
        AdditionalMetricDefinition(
            metric_id="covered_members",
            required_tables=frozenset({"enrolment_months"}),
            time_anchor="enrolment_months.coverage_month",
            tables=("enrolment_months", "members", "plans"),
            join_pairs=(("enrolment_months", "members"), ("members", "plans")),
        ),
        AdditionalMetricDefinition(
            metric_id="open_claim_rate",
            required_tables=frozenset({"claims"}),
            time_anchor="claims.incurred_date",
            tables=("claims", "members", "plans"),
            join_pairs=(("claims", "members"), ("members", "plans")),
        ),
        AdditionalMetricDefinition(
            metric_id="out_of_network_rate",
            required_tables=frozenset({"claim_lines", "providers"}),
            time_anchor="claim_lines.service_date",
            tables=("claim_lines", "claims", "members", "plans", "providers"),
            join_pairs=(
                ("claim_lines", "claims"),
                ("claims", "members"),
                ("members", "plans"),
                ("claim_lines", "providers"),
            ),
        ),
        AdditionalMetricDefinition(
            metric_id="premium_per_member",
            required_tables=frozenset({"premium"}),
            time_anchor="premium.coverage_month",
            tables=("premium", "members", "plans"),
            join_pairs=(("premium", "members"), ("members", "plans")),
        ),
        AdditionalMetricDefinition(
            metric_id="case_reserves",
            required_tables=frozenset({"reserves"}),
            time_anchor="reserves.snapshot_date",
            tables=("reserves", "claims", "members", "plans"),
            join_pairs=(
                ("reserves", "claims"),
                ("claims", "members"),
                ("members", "plans"),
            ),
        ),
    )
}
