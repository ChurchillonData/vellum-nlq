from datetime import date

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest


def test_loss_ratio_query_is_parameterised_and_has_provenance(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    result = build_query(health_uk_catalogue, request)

    assert "WITH claim_totals AS" in result.query.sql
    assert "premium_totals AS" in result.query.sql
    assert "%(start_date)s" in result.query.sql
    assert "%(plan_tier)s" in result.query.sql
    assert "2026-01-01" not in result.query.sql
    assert "Comprehensive" not in result.query.sql
    assert result.query.parameters["start_date"] == date(2026, 1, 1)
    assert result.query.parameters["end_date"] == date(2026, 3, 31)
    assert result.query.parameters["plan_tier"] == "Comprehensive"

    assert result.provenance.metric_id == "loss_ratio"
    assert result.provenance.formula.startswith("SUM(claims.net_incurred_amount)")
    assert result.provenance.tables_used == ("claims", "members", "plans", "premium")
    assert result.provenance.result_shape.grain == "single_metric"
    assert result.validation.passed is True


def test_paid_claims_query_is_parameterised_and_has_provenance(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="paid_claims",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    result = build_query(health_uk_catalogue, request)

    assert "sum(claim_lines.net_paid_amount)" in result.query.sql.lower()
    assert "%(start_date)s" in result.query.sql
    assert "%(plan_tier)s" in result.query.sql
    assert "Comprehensive" not in result.query.sql
    assert result.query.parameters["start_date"] == date(2026, 1, 1)
    assert result.query.parameters["end_date"] == date(2026, 3, 31)
    assert result.query.parameters["plan_tier"] == "Comprehensive"

    assert result.provenance.metric_id == "paid_claims"
    assert result.provenance.time_anchor == "claim_lines.paid_date"
    assert result.provenance.tables_used == (
        "claim_lines",
        "claims",
        "members",
        "plans",
    )
    assert result.provenance.result_shape.columns == ("paid_claims",)
    assert result.validation.passed is True


def test_claim_frequency_query_is_parameterised_and_has_provenance(
    health_uk_catalogue,
) -> None:
    request = AnalyticsRequest(
        metric_id="claim_frequency",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    result = build_query(health_uk_catalogue, request)

    assert "WITH claim_counts AS" in result.query.sql
    assert "member_months AS" in result.query.sql
    assert "count(DISTINCT claims.id)" in result.query.sql
    assert "%(start_date)s" in result.query.sql
    assert "%(plan_tier)s" in result.query.sql
    assert "Comprehensive" not in result.query.sql
    assert result.query.parameters["start_date"] == date(2026, 1, 1)
    assert result.query.parameters["end_date"] == date(2026, 3, 31)
    assert result.query.parameters["plan_tier"] == "Comprehensive"

    assert result.provenance.metric_id == "claim_frequency"
    assert result.provenance.tables_used == (
        "claims",
        "enrolment_months",
        "members",
        "plans",
    )
    assert result.provenance.result_shape.columns == ("claim_frequency",)
    assert result.validation.passed is True


def test_decline_rate_query_is_parameterised_and_has_provenance(
    health_uk_catalogue,
) -> None:
    request = AnalyticsRequest(
        metric_id="decline_rate",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    result = build_query(health_uk_catalogue, request)

    assert "claim_lines.declined_amount" in result.query.sql
    assert "claim_lines.service_date" in result.query.sql
    assert "%(start_date)s" in result.query.sql
    assert "%(plan_tier)s" in result.query.sql
    assert "Comprehensive" not in result.query.sql
    assert result.query.parameters["start_date"] == date(2026, 1, 1)
    assert result.query.parameters["end_date"] == date(2026, 3, 31)
    assert result.query.parameters["plan_tier"] == "Comprehensive"

    assert result.provenance.metric_id == "decline_rate"
    assert result.provenance.time_anchor == "claim_lines.service_date"
    assert result.provenance.tables_used == (
        "claim_lines",
        "claims",
        "members",
        "plans",
    )
    assert result.provenance.result_shape.columns == ("decline_rate",)
    assert result.validation.passed is True
