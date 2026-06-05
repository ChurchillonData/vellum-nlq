from app.analytics.models import QueryBuildResult
from app.metrics.additional import ADDITIONAL_METRICS


def build_demo_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    """Build a concise answer for one executed demo query."""
    if build_result.provenance.metric_id == "claim_frequency":
        return _build_claim_frequency_answer(build_result, rows)
    if build_result.provenance.metric_id == "decline_rate":
        return _build_decline_rate_answer(build_result, rows)
    if build_result.provenance.metric_id == "incurred_claims":
        return _build_incurred_claims_answer(build_result, rows)
    if build_result.provenance.metric_id == "claim_severity":
        return _build_claim_severity_answer(build_result, rows)
    if build_result.provenance.metric_id == "paid_claims":
        return _build_paid_claims_answer(build_result, rows)
    if build_result.provenance.metric_id in ADDITIONAL_METRICS:
        return _build_additional_metric_answer(build_result, rows)
    return _build_loss_ratio_answer(build_result, rows)


def _build_loss_ratio_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    if build_result.plan.group_by:
        return _build_grouped_answer(build_result, rows, "loss ratio")

    value = rows[0].get("loss_ratio") if rows else None
    subject = _subject(build_result, "loss ratio")
    period = _period(build_result)

    if value is None:
        return f"{subject} from {period} could not be calculated because premium was zero."

    ratio = float(value)
    return f"{subject} from {period} was {ratio:.3f} ({ratio:.1%})."


def _build_paid_claims_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    if build_result.plan.group_by:
        return _build_grouped_answer(build_result, rows, "paid claims")

    value = rows[0].get("paid_claims") if rows else None
    subject = _subject(build_result, "paid claims")
    period = _period(build_result)

    if value is None:
        return f"{subject} from {period} had no paid claim amount."

    return f"{subject} from {period} were GBP {float(value):,.2f}."


def _build_incurred_claims_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    if build_result.plan.group_by:
        return _build_grouped_answer(build_result, rows, "incurred claims")

    value = rows[0].get("incurred_claims") if rows else None
    subject = _subject(build_result, "incurred claims")
    period = _period(build_result)

    if value is None:
        return f"{subject} from {period} had no incurred claim amount."

    return f"{subject} from {period} were GBP {float(value):,.2f}."


def _build_claim_frequency_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    if build_result.plan.group_by:
        return _build_grouped_answer(build_result, rows, "claim frequency")

    value = rows[0].get("claim_frequency") if rows else None
    subject = _subject(build_result, "claim frequency")
    period = _period(build_result)

    if value is None:
        return f"{subject} from {period} could not be calculated."

    return f"{subject} from {period} was {float(value):.2f} per 1,000 member months."


def _build_claim_severity_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    if build_result.plan.group_by:
        return _build_grouped_answer(build_result, rows, "claim severity")

    value = rows[0].get("claim_severity") if rows else None
    subject = _subject(build_result, "claim severity")
    period = _period(build_result)

    if value is None:
        return f"{subject} from {period} could not be calculated."

    return f"{subject} from {period} was GBP {float(value):,.2f}."


def _build_decline_rate_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    if build_result.plan.group_by:
        return _build_grouped_answer(build_result, rows, "decline rate")

    value = rows[0].get("decline_rate") if rows else None
    subject = _subject(build_result, "decline rate")
    period = _period(build_result)

    if value is None:
        return f"{subject} from {period} could not be calculated."

    rate = float(value)
    return f"{subject} from {period} was {rate:.3f} ({rate:.1%})."


def _build_additional_metric_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    metric_id = build_result.provenance.metric_id
    metric_label = build_result.provenance.metric_label.casefold()
    if build_result.plan.group_by:
        return _build_grouped_answer(build_result, rows, metric_label)

    value = rows[0].get(metric_id) if rows else None
    subject = _subject(build_result, metric_label)
    period = _period(build_result)
    if value is None:
        return f"{subject} from {period} could not be calculated."

    return f"{subject} from {period} was {_format_metric_value(metric_id, float(value))}."


def _build_grouped_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
    metric_label: str,
) -> str:
    subject = _subject(build_result, metric_label)
    period = _period(build_result)
    group_key = build_result.plan.group_by[0]
    display_group = group_key.replace("_", " ")
    metric_id = build_result.provenance.metric_id

    if not rows:
        return f"{subject} by {display_group} from {period} returned no rows."

    top_row = rows[0]
    group_value = top_row.get(group_key, "Unknown")
    value = float(top_row.get(metric_id) or 0)
    return (
        f"{subject} by {display_group} from {period} was highest for "
        f"{group_value} at {_format_metric_value(metric_id, value)}."
    )


def _format_metric_value(metric_id: str, value: float) -> str:
    if metric_id in {
        "loss_ratio",
        "decline_rate",
        "open_claim_rate",
        "out_of_network_rate",
    }:
        return f"{value:.3f} ({value:.1%})"
    if metric_id in {
        "paid_claims",
        "incurred_claims",
        "claim_severity",
        "premium_per_member",
        "case_reserves",
    }:
        return f"GBP {value:,.2f}"
    if metric_id == "claim_frequency":
        return f"{value:.2f} per 1,000 member months"
    if metric_id in {"claim_count", "covered_members"}:
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def _subject(build_result: QueryBuildResult, metric_label: str) -> str:
    plan_tier = build_result.plan.plan_tier
    if plan_tier:
        return f"{plan_tier} plan tier {metric_label}"
    return metric_label.capitalize()


def _period(build_result: QueryBuildResult) -> str:
    return (
        f"{build_result.plan.start_date.isoformat()} "
        f"to {build_result.plan.end_date.isoformat()}"
    )
