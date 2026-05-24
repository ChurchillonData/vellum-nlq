from app.analytics.models import ResultShape


GROUPED_RESULT_LIMIT = 50
COMMON_GROUPINGS = {"plan_tier", "region"}


def result_shape(metric_id: str, group_by: tuple[str, ...]) -> ResultShape:
    """Return the expected result shape for grouped or ungrouped output."""
    if not group_by:
        return ResultShape(columns=(metric_id,), grain="single_metric")

    group_key = group_by[0]
    return ResultShape(
        columns=(group_key, metric_id),
        grain=group_key,
        max_rows=GROUPED_RESULT_LIMIT,
    )


def grouping_is_supported(metric_id: str, group_by: tuple[str, ...]) -> bool:
    """Return whether a metric supports the requested grouped demo output."""
    if not group_by:
        return True

    if len(group_by) != 1:
        return False

    group_key = group_by[0]
    if group_key in COMMON_GROUPINGS:
        return True

    return metric_id == "decline_rate" and group_key == "consultant_specialty"
