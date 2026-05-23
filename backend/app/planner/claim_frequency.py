from app.analytics.models import LogicalPlan, ResolvedRequest, ResultShape
from app.planner.joins import find_join
from app.semantic.models import Catalogue


def build_claim_frequency_plan(
    catalogue: Catalogue,
    resolved: ResolvedRequest,
) -> LogicalPlan:
    """Plan claim frequency per thousand member months."""
    request = resolved.request
    joins = (
        find_join(catalogue, "claims", "members"),
        find_join(catalogue, "enrolment_months", "members"),
        find_join(catalogue, "members", "plans"),
    )

    filters = [
        f"{resolved.metric.time_anchor} between start_date and end_date",
        "enrolment_months.coverage_month between start_date and end_date",
        *resolved.metric.filters_default,
    ]
    if request.plan_tier:
        filters.append("plans.plan_tier = plan_tier")

    return LogicalPlan(
        metric=resolved.metric,
        start_date=request.start_date,
        end_date=request.end_date,
        plan_tier=request.plan_tier,
        group_by=request.group_by,
        tables=("claims", "enrolment_months", "members", "plans"),
        joins=joins,
        filters=tuple(filters),
        result_shape=ResultShape(columns=("claim_frequency",), grain="single_metric"),
    )
