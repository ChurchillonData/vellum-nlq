from datetime import date

import pytest

from app.analytics.models import AnalyticsRequest
from app.semantic.resolver import ResolutionError, resolve_request


def test_resolver_returns_loss_ratio_metric(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    resolved = resolve_request(health_uk_catalogue, request)

    assert resolved.metric.id == "loss_ratio"
    assert resolved.metric.time_anchor == "claims.incurred_date"
    assert resolved.request.plan_tier == "Comprehensive"


def test_resolver_returns_paid_claims_metric(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="paid_claims",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    resolved = resolve_request(health_uk_catalogue, request)

    assert resolved.metric.id == "paid_claims"
    assert resolved.metric.time_anchor == "claim_lines.paid_date"


def test_resolver_returns_claim_frequency_metric(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="claim_frequency",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    resolved = resolve_request(health_uk_catalogue, request)

    assert resolved.metric.id == "claim_frequency"
    assert resolved.metric.time_anchor == "claims.incurred_date"


def test_resolver_returns_decline_rate_metric(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="decline_rate",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    resolved = resolve_request(health_uk_catalogue, request)

    assert resolved.metric.id == "decline_rate"
    assert resolved.metric.time_anchor == "claim_lines.service_date"


def test_resolver_accepts_decline_rate_consultant_specialty_grouping(
    health_uk_catalogue,
) -> None:
    request = AnalyticsRequest(
        metric_id="decline_rate",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("consultant_specialty",),
    )

    resolved = resolve_request(health_uk_catalogue, request)

    assert resolved.request.group_by == ("consultant_specialty",)


def test_resolver_rejects_unsupported_grouping(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("consultant_specialty",),
    )

    with pytest.raises(ResolutionError, match="grouping is not supported"):
        resolve_request(health_uk_catalogue, request)


def test_resolver_rejects_unknown_metric(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="unknown_metric",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    )

    with pytest.raises(ResolutionError, match="unknown metric"):
        resolve_request(health_uk_catalogue, request)
