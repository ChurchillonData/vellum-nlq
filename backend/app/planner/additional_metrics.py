from app.analytics.models import LogicalPlan, ResolvedRequest
from app.metrics.additional import ADDITIONAL_METRICS
from app.planner.grouping import result_shape
from app.planner.joins import find_join
from app.semantic.models import Catalogue


def build_additional_metric_plan(
    catalogue: Catalogue,
    resolved: ResolvedRequest,
) -> LogicalPlan:
    """Plan one governed aggregate metric backed by existing tables and joins."""
    request = resolved.request
    definition = ADDITIONAL_METRICS[resolved.metric.id]
    filters = [
        f"{resolved.metric.time_anchor} between start_date and end_date",
        *definition.extra_filters,
    ]
    if request.plan_tier:
        filters.append("plans.plan_tier = plan_tier")

    return LogicalPlan(
        metric=resolved.metric,
        start_date=request.start_date,
        end_date=request.end_date,
        plan_tier=request.plan_tier,
        group_by=request.group_by,
        tables=definition.tables,
        joins=tuple(
            find_join(catalogue, left_table, right_table)
            for left_table, right_table in definition.join_pairs
        ),
        filters=tuple(filters),
        result_shape=result_shape(resolved.metric.id, request.group_by),
    )
