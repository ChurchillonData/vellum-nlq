from app.analytics.models import AnalyticsRequest, ResolvedRequest
from app.planner.grouping import grouping_is_supported
from app.semantic.models import Catalogue, MetricSpec


class ResolutionError(ValueError):
    """Raised when a structured request cannot be resolved yet."""


SUPPORTED_METRICS = {
    "loss_ratio",
    "paid_claims",
    "claim_frequency",
    "decline_rate",
    "incurred_claims",
    "claim_severity",
}


def resolve_request(catalogue: Catalogue, request: AnalyticsRequest) -> ResolvedRequest:
    """Resolve a structured request against the loaded semantic catalogue."""
    metric = catalogue.metrics.get(request.metric_id)
    if metric is None:
        raise ResolutionError(f"unknown metric: {request.metric_id}")

    if metric.id not in SUPPORTED_METRICS:
        raise ResolutionError(f"metric is not implemented yet: {metric.id}")

    _validate_group_by(metric, request.group_by)

    if metric.id == "loss_ratio":
        _validate_loss_ratio_metric(metric)
    if metric.id == "paid_claims":
        _validate_paid_claims_metric(metric)
    if metric.id == "claim_frequency":
        _validate_claim_frequency_metric(metric)
    if metric.id == "decline_rate":
        _validate_decline_rate_metric(metric)
    if metric.id == "incurred_claims":
        _validate_incurred_claims_metric(metric)
    if metric.id == "claim_severity":
        _validate_claim_severity_metric(metric)

    return ResolvedRequest(request=request, metric=metric)


def _validate_loss_ratio_metric(metric: MetricSpec) -> None:
    if metric.time_anchor != "claims.incurred_date":
        raise ResolutionError(
            f"loss_ratio expects claims.incurred_date, found {metric.time_anchor}"
        )

    if set(metric.required_tables) != {"claims", "premium"}:
        raise ResolutionError("loss_ratio requires claims and premium")


def _validate_paid_claims_metric(metric: MetricSpec) -> None:
    if metric.time_anchor != "claim_lines.paid_date":
        raise ResolutionError(
            f"paid_claims expects claim_lines.paid_date, found {metric.time_anchor}"
        )

    if set(metric.required_tables) != {"claim_lines"}:
        raise ResolutionError("paid_claims requires claim_lines")


def _validate_claim_frequency_metric(metric: MetricSpec) -> None:
    if metric.time_anchor != "claims.incurred_date":
        raise ResolutionError(
            f"claim_frequency expects claims.incurred_date, found {metric.time_anchor}"
        )

    if set(metric.required_tables) != {"claims", "enrolment_months"}:
        raise ResolutionError("claim_frequency requires claims and enrolment_months")


def _validate_decline_rate_metric(metric: MetricSpec) -> None:
    if metric.time_anchor != "claim_lines.service_date":
        raise ResolutionError(
            f"decline_rate expects claim_lines.service_date, found {metric.time_anchor}"
        )

    if set(metric.required_tables) != {"claim_lines"}:
        raise ResolutionError("decline_rate requires claim_lines")


def _validate_incurred_claims_metric(metric: MetricSpec) -> None:
    if metric.time_anchor != "claims.incurred_date":
        raise ResolutionError(
            f"incurred_claims expects claims.incurred_date, found {metric.time_anchor}"
        )

    if set(metric.required_tables) != {"claims"}:
        raise ResolutionError("incurred_claims requires claims")


def _validate_claim_severity_metric(metric: MetricSpec) -> None:
    if metric.time_anchor != "claim_lines.paid_date":
        raise ResolutionError(
            f"claim_severity expects claim_lines.paid_date, found {metric.time_anchor}"
        )

    if set(metric.required_tables) != {"claims", "claim_lines"}:
        raise ResolutionError("claim_severity requires claims and claim_lines")


def _validate_group_by(metric: MetricSpec, group_by: tuple[str, ...]) -> None:
    if grouping_is_supported(metric.id, group_by):
        return

    group_list = ", ".join(group_by)
    raise ResolutionError(f"grouping is not supported for {metric.id}: {group_list}")
