from app.analytics.models import LogicalPlan, ResolvedRequest
from app.planner.grouping import result_shape
from app.planner.joins import find_join
from app.semantic.models import Catalogue


def build_decline_rate_plan(catalogue: Catalogue, resolved: ResolvedRequest) -> LogicalPlan:
    """Plan ungrouped decline rate with optional plan-tier filtering."""
    request = resolved.request
    joins = [
        find_join(catalogue, "claim_lines", "claims"),
        find_join(catalogue, "claims", "members"),
        find_join(catalogue, "members", "plans"),
    ]
    tables = ["claim_lines", "claims", "members", "plans"]

    filters = [f"{resolved.metric.time_anchor} between start_date and end_date"]
    if request.plan_tier:
        filters.append("plans.plan_tier = plan_tier")

    shape = result_shape("decline_rate", request.group_by)
    if request.group_by == ("consultant_specialty",):
        joins.append(find_join(catalogue, "claim_lines", "providers"))
        tables.append("providers")

    return LogicalPlan(
        metric=resolved.metric,
        start_date=request.start_date,
        end_date=request.end_date,
        plan_tier=request.plan_tier,
        group_by=request.group_by,
        tables=tuple(tables),
        joins=tuple(joins),
        filters=tuple(filters),
        result_shape=shape,
    )
