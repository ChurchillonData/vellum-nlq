from datetime import date

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest
from app.sql.guard import validate_sql


def test_guard_accepts_generated_loss_ratio_sql(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    result = build_query(health_uk_catalogue, request)

    assert result.validation.passed is True
    assert result.validation.rejections == ()
    assert result.validation.rules_checked == (
        "comments_absent",
        "parseable_sql",
        "single_statement",
        "select_only",
        "system_schema_absent",
    )


def test_guard_rejects_non_select_statement() -> None:
    result = validate_sql("DROP TABLE claims")

    assert result.passed is False
    assert result.rejections[0].rule == "select_only"


def test_guard_rejects_multiple_statements() -> None:
    result = validate_sql("SELECT 1; DROP TABLE claims")

    assert result.passed is False
    assert result.rejections[0].rule == "single_statement"


def test_guard_rejects_system_schema_reference() -> None:
    result = validate_sql("SELECT table_name FROM pg_catalog.pg_tables")

    assert result.passed is False
    assert result.rejections[0].rule == "system_schema_absent"


def test_guard_rejects_sql_comments() -> None:
    result = validate_sql("SELECT 1 -- hidden payload")

    assert result.passed is False
    assert result.rejections[0].rule == "comments_absent"
