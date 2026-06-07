from app.analytics.models import ResultShape


GROUPED_RESULT_LIMIT = 50
COMMON_GROUPINGS = {"month", "plan_tier", "region"}
LINE_LEVEL_DIAGNOSIS_METRICS = {
    "claim_severity",
    "decline_rate",
    "out_of_network_rate",
    "paid_claims",
}
SPECIALTY_GROUPING_METRICS = {"decline_rate"}


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

    if group_key == "diagnosis_category":
        return metric_id in LINE_LEVEL_DIAGNOSIS_METRICS
    if group_key == "consultant_specialty":
        return metric_id in SPECIALTY_GROUPING_METRICS
    return False


def supported_groupings_for_metric(metric_id: str) -> list[str]:
    """Return deterministic groupings exposed for one metric."""
    dimensions = set(COMMON_GROUPINGS)
    if metric_id in LINE_LEVEL_DIAGNOSIS_METRICS:
        dimensions.add("diagnosis_category")
    if metric_id in SPECIALTY_GROUPING_METRICS:
        dimensions.add("consultant_specialty")
    return sorted(dimensions)
