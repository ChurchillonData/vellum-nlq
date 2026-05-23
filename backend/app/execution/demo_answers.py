from app.analytics.models import QueryBuildResult


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
    return _build_loss_ratio_answer(build_result, rows)


def _build_loss_ratio_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
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
    if build_result.plan.group_by == ("consultant_specialty",):
        return _build_grouped_decline_rate_answer(build_result, rows)

    value = rows[0].get("decline_rate") if rows else None
    subject = _subject(build_result, "decline rate")
    period = _period(build_result)

    if value is None:
        return f"{subject} from {period} could not be calculated."

    rate = float(value)
    return f"{subject} from {period} was {rate:.3f} ({rate:.1%})."


def _build_grouped_decline_rate_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    subject = _subject(build_result, "decline rate")
    period = _period(build_result)

    if not rows:
        return f"{subject} by consultant specialty from {period} returned no rows."

    top_row = rows[0]
    specialty = top_row.get("consultant_specialty", "Unknown")
    rate = float(top_row.get("decline_rate") or 0)
    return (
        f"{subject} by consultant specialty from {period} was highest for "
        f"{specialty} at {rate:.3f} ({rate:.1%})."
    )


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
