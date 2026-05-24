from app.analytics.models import LogicalPlan, ResolvedRequest
from app.planner.grouping import result_shape
from app.planner.joins import find_join
from app.semantic.models import Catalogue


def build_claim_severity_plan(
    catalogue: Catalogue,
    resolved: ResolvedRequest,
) -> LogicalPlan:
    """Plan average paid claim severity with optional plan-tier filtering."""
    request = resolved.request
    joins = (
        find_join(catalogue, "claim_lines", "claims"),
        find_join(catalogue, "claims", "members"),
        find_join(catalogue, "members", "plans"),
    )

    filters = [
        f"{resolved.metric.time_anchor} between start_date and end_date",
        "claims.status = closed_status",
    ]
    if request.plan_tier:
        filters.append("plans.plan_tier = plan_tier")

    return LogicalPlan(
        metric=resolved.metric,
        start_date=request.start_date,
        end_date=request.end_date,
        plan_tier=request.plan_tier,
        group_by=request.group_by,
        tables=("claim_lines", "claims", "members", "plans"),
        joins=joins,
        filters=tuple(filters),
        result_shape=result_shape("claim_severity", request.group_by),
    )
