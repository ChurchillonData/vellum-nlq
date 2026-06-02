from app.analytics.models import AnalyticsRequest, QueryBuildResult, QueryProvenance
from app.planner.claim_severity import build_claim_severity_plan
from app.planner.claim_frequency import build_claim_frequency_plan
from app.planner.decline_rate import build_decline_rate_plan
from app.planner.incurred_claims import build_incurred_claims_plan
from app.planner.loss_ratio import build_loss_ratio_plan
from app.planner.paid_claims import build_paid_claims_plan
from app.semantic.models import Catalogue, JoinEdge
from app.semantic.resolver import resolve_request
from app.sql.generator import (
    generate_claim_frequency_query,
    generate_claim_severity_query,
    generate_decline_rate_query,
    generate_incurred_claims_query,
    generate_loss_ratio_query,
    generate_paid_claims_query,
)
from app.sql.guard import validate_sql


def build_query(catalogue: Catalogue, request: AnalyticsRequest) -> QueryBuildResult:
    """Build one deterministic query with provenance and no database execution."""
    resolved = resolve_request(catalogue, request)
    if resolved.metric.id == "loss_ratio":
        plan = build_loss_ratio_plan(catalogue, resolved)
        query = generate_loss_ratio_query(plan)
    elif resolved.metric.id == "paid_claims":
        plan = build_paid_claims_plan(catalogue, resolved)
        query = generate_paid_claims_query(plan)
    elif resolved.metric.id == "claim_frequency":
        plan = build_claim_frequency_plan(catalogue, resolved)
        query = generate_claim_frequency_query(plan)
    elif resolved.metric.id == "decline_rate":
        plan = build_decline_rate_plan(catalogue, resolved)
        query = generate_decline_rate_query(plan)
    elif resolved.metric.id == "incurred_claims":
        plan = build_incurred_claims_plan(catalogue, resolved)
        query = generate_incurred_claims_query(plan)
    elif resolved.metric.id == "claim_severity":
        plan = build_claim_severity_plan(catalogue, resolved)
        query = generate_claim_severity_query(plan)
    else:
        raise ValueError(f"metric is not implemented yet: {resolved.metric.id}")

    validation = validate_sql(query.sql, catalogue, query.parameters)
    provenance = QueryProvenance(
        metric_id=plan.metric.id,
        metric_label=plan.metric.label,
        metric_version=plan.metric.version,
        metric_description=plan.metric.description,
        formula=plan.metric.formula.expression,
        time_anchor=plan.metric.time_anchor,
        tables_used=plan.tables,
        joins_used=tuple(_describe_join(join) for join in plan.joins),
        result_shape=plan.result_shape,
    )
    return QueryBuildResult(
        plan=plan,
        query=query,
        provenance=provenance,
        validation=validation,
    )


def _describe_join(join: JoinEdge) -> str:
    return (
        f"{join.left_table}.{join.left_column} = "
        f"{join.right_table}.{join.right_column} "
        f"({join.cardinality})"
    )
