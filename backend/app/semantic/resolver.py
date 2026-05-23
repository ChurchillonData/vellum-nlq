from app.analytics.models import AnalyticsRequest, ResolvedRequest
from app.semantic.models import Catalogue, MetricSpec


class ResolutionError(ValueError):
    """Raised when a structured request cannot be resolved yet."""


SUPPORTED_METRICS = {"loss_ratio", "paid_claims", "claim_frequency"}


def resolve_request(catalogue: Catalogue, request: AnalyticsRequest) -> ResolvedRequest:
    """Resolve a structured request against the loaded semantic catalogue."""
    metric = catalogue.metrics.get(request.metric_id)
    if metric is None:
        raise ResolutionError(f"unknown metric: {request.metric_id}")

    if metric.id not in SUPPORTED_METRICS:
        raise ResolutionError(f"metric is not implemented yet: {metric.id}")

    if metric.id == "loss_ratio":
        _validate_loss_ratio_metric(metric)
    if metric.id == "paid_claims":
        _validate_paid_claims_metric(metric)
    if metric.id == "claim_frequency":
        _validate_claim_frequency_metric(metric)

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
