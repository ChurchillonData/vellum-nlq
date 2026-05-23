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
        "table_allowlist",
        "column_allowlist",
        "function_allowlist",
        "parameter_literal_enforcement",
        "join_allowlist",
        "result_size_control",
    )


def test_guard_rejects_non_select_statement(health_uk_catalogue) -> None:
    result = validate_sql("DROP TABLE claims", health_uk_catalogue)

    assert result.passed is False
    assert result.rejections[0].rule == "select_only"


def test_guard_rejects_multiple_statements(health_uk_catalogue) -> None:
    result = validate_sql("SELECT 1; DROP TABLE claims", health_uk_catalogue)

    assert result.passed is False
    assert result.rejections[0].rule == "single_statement"


def test_guard_rejects_system_schema_reference(health_uk_catalogue) -> None:
    result = validate_sql(
        "SELECT table_name FROM pg_catalog.pg_tables",
        health_uk_catalogue,
    )

    assert result.passed is False
    assert result.rejections[0].rule == "system_schema_absent"


def test_guard_rejects_sql_comments(health_uk_catalogue) -> None:
    result = validate_sql("SELECT 1 -- hidden payload", health_uk_catalogue)

    assert result.passed is False
    assert result.rejections[0].rule == "comments_absent"


def test_guard_rejects_unknown_table(health_uk_catalogue) -> None:
    result = validate_sql("SELECT users.id FROM users", health_uk_catalogue)

    assert result.passed is False
    assert result.rejections[0].rule == "table_allowlist"


def test_guard_rejects_unknown_column(health_uk_catalogue) -> None:
    result = validate_sql(
        "SELECT claims.secret_notes FROM claims",
        health_uk_catalogue,
    )

    assert result.passed is False
    assert result.rejections[0].rule == "column_allowlist"


def test_guard_rejects_disallowed_function(health_uk_catalogue) -> None:
    result = validate_sql("SELECT pg_sleep(1) FROM claims", health_uk_catalogue)

    assert result.passed is False
    assert result.rejections[0].rule == "function_allowlist"


def test_guard_rejects_unapproved_physical_join(health_uk_catalogue) -> None:
    result = validate_sql(
        "SELECT claims.id FROM claims "
        "JOIN plans ON claims.member_id = plans.id",
        health_uk_catalogue,
    )

    assert result.passed is False
    assert result.rejections[0].rule == "join_allowlist"


def test_guard_rejects_embedded_string_literals(health_uk_catalogue) -> None:
    result = validate_sql(
        "SELECT claims.id FROM claims WHERE claims.status = 'closed'",
        health_uk_catalogue,
    )

    assert result.passed is False
    assert result.rejections[0].rule == "parameter_literal_enforcement"


def test_guard_rejects_grouped_query_without_limit(health_uk_catalogue) -> None:
    result = validate_sql(
        "SELECT providers.specialty, COUNT(claim_lines.id) "
        "FROM claim_lines "
        "JOIN providers ON claim_lines.provider_id = providers.id "
        "GROUP BY providers.specialty",
        health_uk_catalogue,
    )

    assert result.passed is False
    assert result.rejections[0].rule == "result_size_control"


def test_guard_rejects_grouped_query_limit_over_cap(health_uk_catalogue) -> None:
    result = validate_sql(
        "SELECT providers.specialty, COUNT(claim_lines.id) "
        "FROM claim_lines "
        "JOIN providers ON claim_lines.provider_id = providers.id "
        "GROUP BY providers.specialty "
        "LIMIT 500",
        health_uk_catalogue,
    )

    assert result.passed is False
    assert result.rejections[0].rule == "result_size_control"
