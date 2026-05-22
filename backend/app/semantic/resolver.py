from app.analytics.models import AnalyticsRequest, ResolvedRequest
from app.semantic.models import Catalogue


class ResolutionError(ValueError):
    """Raised when a structured request cannot be resolved yet."""


SUPPORTED_METRICS = {"loss_ratio"}


def resolve_request(catalogue: Catalogue, request: AnalyticsRequest) -> ResolvedRequest:
    """Resolve a structured request against the loaded semantic catalogue."""
    metric = catalogue.metrics.get(request.metric_id)
    if metric is None:
        raise ResolutionError(f"unknown metric: {request.metric_id}")

    if metric.id not in SUPPORTED_METRICS:
        raise ResolutionError(f"metric is not implemented yet: {metric.id}")

    if metric.time_anchor != "claims.incurred_date":
        raise ResolutionError(
            f"loss_ratio expects claims.incurred_date, found {metric.time_anchor}"
        )

    required_tables = set(metric.required_tables)
    if required_tables != {"claims", "premium"}:
        raise ResolutionError(
            "loss_ratio requires claims and premium in the current planner"
        )

    return ResolvedRequest(request=request, metric=metric)

