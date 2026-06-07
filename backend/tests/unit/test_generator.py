from datetime import date

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest
from app.metrics.additional import ADDITIONAL_METRICS


def _parameter_placeholders(sql: str) -> set[str]:
    """Return parameter names referenced by SQLAlchemy's PostgreSQL placeholders."""
    return {
        token.split(")s", 1)[0]
        for token in sql.split("%(")[1:]
        if ")s" in token
    }


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
    assert "FROM claim_totals JOIN premium_totals ON true" in result.query.sql
    assert "GROUP BY claims.member_id" not in result.query.sql
    assert "GROUP BY premium.member_id" not in result.query.sql
    assert "%(start_date)s" in result.query.sql
    assert "%(plan_tier)s" in result.query.sql
    assert "2026-01-01" not in result.query.sql
    assert "Comprehensive" not in result.query.sql
    assert result.query.parameters["start_date"] == date(2026, 1, 1)
    assert result.query.parameters["end_date"] == date(2026, 3, 31)
    assert result.query.parameters["plan_tier"] == "Comprehensive"
    assert "WITH claim_totals AS" not in result.query.compact_sql
    assert "JOIN" not in result.query.compact_sql
    assert "semantic.loss_ratio_base" in result.query.compact_sql
    assert "%(start_date)s" in result.query.compact_sql
    assert "%(plan_tier)s" in result.query.compact_sql
    assert "Comprehensive" not in result.query.compact_sql
    assert len(result.query.compact_sql.splitlines()) <= 7

    assert result.provenance.metric_id == "loss_ratio"
    assert result.provenance.formula.startswith("SUM(claims.net_incurred_amount)")
    assert result.provenance.tables_used == ("claims", "members", "plans", "premium")
    assert result.provenance.result_shape.grain == "single_metric"
    assert result.provenance.result_shape.max_rows == 1
    assert result.validation.passed is True


def test_compact_sql_uses_only_explainable_pipeline_parameters(
    health_uk_catalogue,
) -> None:
    requests = [
        AnalyticsRequest(
            metric_id="loss_ratio",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            plan_tier="Comprehensive",
        ),
        AnalyticsRequest(
            metric_id="paid_claims",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            group_by=("region",),
        ),
        AnalyticsRequest(
            metric_id="claim_severity",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            plan_tier="Executive",
        ),
        AnalyticsRequest(
            metric_id="decline_rate",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            group_by=("consultant_specialty",),
        ),
    ]

    for request in requests:
        result = build_query(health_uk_catalogue, request)
        compact_params = _parameter_placeholders(result.query.compact_sql)

        assert compact_params
        assert compact_params <= set(result.query.parameters)
        assert compact_params <= _parameter_placeholders(result.query.sql)


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
    assert "semantic.claim_payments" in result.query.compact_sql
    assert "JOIN" not in result.query.compact_sql
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
    assert result.provenance.result_shape.max_rows == 1
    assert result.validation.passed is True


def test_incurred_claims_query_is_parameterised_and_has_provenance(
    health_uk_catalogue,
) -> None:
    request = AnalyticsRequest(
        metric_id="incurred_claims",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    result = build_query(health_uk_catalogue, request)

    assert "sum(claims.net_incurred_amount)" in result.query.sql.lower()
    assert "%(start_date)s" in result.query.sql
    assert "%(excluded_status)s" in result.query.sql
    assert "%(plan_tier)s" in result.query.sql
    assert "Comprehensive" not in result.query.sql
    assert result.query.parameters["start_date"] == date(2026, 1, 1)
    assert result.query.parameters["end_date"] == date(2026, 3, 31)
    assert result.query.parameters["excluded_status"] == "void"
    assert result.query.parameters["plan_tier"] == "Comprehensive"

    assert result.provenance.metric_id == "incurred_claims"
    assert result.provenance.time_anchor == "claims.incurred_date"
    assert result.provenance.tables_used == ("claims", "members", "plans")
    assert result.provenance.result_shape.columns == ("incurred_claims",)
    assert result.provenance.result_shape.max_rows == 1
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
    assert result.provenance.result_shape.max_rows == 1
    assert result.validation.passed is True


def test_claim_severity_query_is_parameterised_and_has_provenance(
    health_uk_catalogue,
) -> None:
    request = AnalyticsRequest(
        metric_id="claim_severity",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    result = build_query(health_uk_catalogue, request)

    assert "sum(claim_lines.net_paid_amount)" in result.query.sql.lower()
    assert "count(DISTINCT claims.id)" in result.query.sql
    assert "%(closed_status)s" in result.query.sql
    assert "%(plan_tier)s" in result.query.sql
    assert "'closed'" not in result.query.sql
    assert "Comprehensive" not in result.query.sql
    assert result.query.parameters["closed_status"] == "closed"
    assert result.query.parameters["plan_tier"] == "Comprehensive"

    assert result.provenance.metric_id == "claim_severity"
    assert result.provenance.time_anchor == "claim_lines.paid_date"
    assert result.provenance.tables_used == (
        "claim_lines",
        "claims",
        "members",
        "plans",
    )
    assert result.provenance.result_shape.columns == ("claim_severity",)
    assert result.provenance.result_shape.max_rows == 1
    assert result.validation.passed is True


def test_additional_governed_metric_queries_are_guarded_and_explainable(
    health_uk_catalogue,
) -> None:
    for metric_id in ADDITIONAL_METRICS:
        request = AnalyticsRequest(
            metric_id=metric_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            plan_tier="Comprehensive",
        )

        result = build_query(health_uk_catalogue, request)

        assert result.provenance.metric_id == metric_id
        assert result.provenance.result_shape.columns == (metric_id,)
        assert result.validation.passed is True
        assert "%(start_date)s" in result.query.sql
        assert "%(end_date)s" in result.query.sql
        assert "Comprehensive" not in result.query.sql
        assert "JOIN" not in result.query.compact_sql
        assert metric_id in result.query.compact_sql


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
    assert result.provenance.result_shape.max_rows == 1
    assert result.validation.passed is True


def test_decline_rate_query_groups_by_consultant_specialty(
    health_uk_catalogue,
) -> None:
    request = AnalyticsRequest(
        metric_id="decline_rate",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("consultant_specialty",),
    )

    result = build_query(health_uk_catalogue, request)

    assert "providers.specialty AS consultant_specialty" in result.query.sql
    assert "GROUP BY providers.specialty" in result.query.sql
    assert "ORDER BY CAST(sum" in result.query.sql
    assert "LIMIT %(result_limit)s" in result.query.sql
    assert result.query.parameters["result_limit"] == 50
    assert result.provenance.tables_used == (
        "claim_lines",
        "claims",
        "members",
        "plans",
        "providers",
    )
    assert result.provenance.result_shape.columns == (
        "consultant_specialty",
        "decline_rate",
    )
    assert result.provenance.result_shape.grain == "consultant_specialty"
    assert result.provenance.result_shape.max_rows == 50
    assert result.validation.passed is True


def test_loss_ratio_query_groups_by_plan_tier(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("plan_tier",),
    )

    result = build_query(health_uk_catalogue, request)

    assert "plans.plan_tier AS plan_tier" in result.query.sql
    assert "GROUP BY plans.plan_tier" in result.query.sql
    assert "LIMIT %(result_limit)s" in result.query.sql
    assert result.query.parameters["result_limit"] == 50
    assert result.provenance.result_shape.columns == ("plan_tier", "loss_ratio")
    assert result.provenance.result_shape.grain == "plan_tier"
    assert result.provenance.result_shape.max_rows == 50
    assert result.validation.passed is True


def test_paid_claims_query_groups_by_region(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="paid_claims",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("region",),
    )

    result = build_query(health_uk_catalogue, request)

    assert "members.region AS region" in result.query.sql
    assert "GROUP BY members.region" in result.query.sql
    assert "LIMIT %(result_limit)s" in result.query.sql
    assert result.query.parameters["result_limit"] == 50
    assert result.provenance.result_shape.columns == ("region", "paid_claims")
    assert result.provenance.result_shape.max_rows == 50
    assert result.validation.passed is True


def test_loss_ratio_query_groups_by_month(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("month",),
    )

    result = build_query(health_uk_catalogue, request)

    assert "date_trunc(%(date_trunc_1)s, claims.incurred_date) AS month" in result.query.sql
    assert "date_trunc(%(date_trunc_2)s, premium.coverage_month) AS month" in result.query.sql
    assert result.query.parameters["date_trunc_1"] == "month"
    assert result.query.parameters["date_trunc_2"] == "month"
    assert result.query.parameters["result_limit"] == 50
    assert result.provenance.result_shape.columns == ("month", "loss_ratio")
    assert result.provenance.result_shape.grain == "month"
    assert result.validation.passed is True


def test_paid_claims_query_groups_by_diagnosis_category(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="paid_claims",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("diagnosis_category",),
    )

    result = build_query(health_uk_catalogue, request)

    assert "claim_lines.diagnosis_category AS diagnosis_category" in result.query.sql
    assert "GROUP BY claim_lines.diagnosis_category" in result.query.sql
    assert result.query.parameters["result_limit"] == 50
    assert result.provenance.result_shape.columns == (
        "diagnosis_category",
        "paid_claims",
    )
    assert result.provenance.result_shape.grain == "diagnosis_category"
    assert result.validation.passed is True
