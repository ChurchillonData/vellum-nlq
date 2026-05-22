from app.analytics.models import LogicalPlan, ResolvedRequest, ResultShape
from app.semantic.models import Catalogue, JoinEdge


class PlanningError(ValueError):
    """Raised when a requested plan cannot be built from catalogue joins."""


def build_loss_ratio_plan(catalogue: Catalogue, resolved: ResolvedRequest) -> LogicalPlan:
    """Plan loss ratio with supporting member and plan joins."""
    request = resolved.request
    joins = (
        _find_join(catalogue, "claims", "members"),
        _find_join(catalogue, "premium", "members"),
        _find_join(catalogue, "members", "plans"),
    )

    filters = [
        f"{resolved.metric.time_anchor} between start_date and end_date",
        "premium.coverage_month between start_date and end_date",
        *resolved.metric.filters_default,
    ]
    if request.plan_tier:
        filters.append("plans.plan_tier = plan_tier")

    return LogicalPlan(
        metric=resolved.metric,
        start_date=request.start_date,
        end_date=request.end_date,
        plan_tier=request.plan_tier,
        tables=("claims", "members", "plans", "premium"),
        joins=joins,
        filters=tuple(filters),
        result_shape=ResultShape(columns=("loss_ratio",), grain="single_metric"),
    )


def _find_join(catalogue: Catalogue, left_table: str, right_table: str) -> JoinEdge:
    for join in catalogue.joins:
        tables = {join.left_table, join.right_table}
        if tables == {left_table, right_table}:
            return join

    raise PlanningError(f"missing approved join between {left_table} and {right_table}")

