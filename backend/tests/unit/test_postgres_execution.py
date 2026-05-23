from datetime import date

import pytest

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest
from app.config import Settings
from app.execution.factory import execute_query
from app.execution.postgres import execute_postgres_query
from app.sql.guard import SqlGuardRejection, SqlGuardResult


def test_postgres_executor_refuses_failed_guard_result(health_uk_catalogue) -> None:
    build_result = build_query(
        health_uk_catalogue,
        AnalyticsRequest(
            metric_id="loss_ratio",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
        ),
    )
    unsafe_result = build_result.__class__(
        plan=build_result.plan,
        query=build_result.query,
        provenance=build_result.provenance,
        validation=SqlGuardResult(
            passed=False,
            rules_checked=("select_only",),
            rejections=(
                SqlGuardRejection(rule="select_only", message="Only SELECT."),
            ),
        ),
    )

    with pytest.raises(ValueError, match="failed guard validation"):
        execute_postgres_query(unsafe_result, "postgresql+psycopg://readonly")


def test_postgres_executor_uses_bound_parameters(monkeypatch, health_uk_catalogue) -> None:
    captured = {}
    build_result = build_query(
        health_uk_catalogue,
        AnalyticsRequest(
            metric_id="loss_ratio",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            plan_tier="Comprehensive",
        ),
    )

    class FakeRow:
        _mapping = {"loss_ratio": 0.84}

    class FakeResult:
        def fetchall(self):
            return [FakeRow()]

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, parameters):
            captured["statement"] = statement
            captured["parameters"] = parameters
            return FakeResult()

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    def fake_create_engine(url):
        captured["url"] = url
        return FakeEngine()

    monkeypatch.setattr("app.execution.postgres.create_engine", fake_create_engine)

    result = execute_postgres_query(build_result, "postgresql+psycopg://readonly")

    assert captured["url"] == "postgresql+psycopg://readonly"
    assert captured["parameters"]["plan_tier"] == "Comprehensive"
    assert "Comprehensive" not in str(captured["statement"])
    assert result.mode == "postgres"
    assert result.dataset.name == "health-uk postgres"
    assert result.row_count == 1
    assert result.rows == [{"loss_ratio": 0.84}]


def test_postgres_executor_caps_rows(monkeypatch, health_uk_catalogue) -> None:
    build_result = build_query(
        health_uk_catalogue,
        AnalyticsRequest(
            metric_id="decline_rate",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            group_by=("consultant_specialty",),
        ),
    )

    class FakeRow:
        def __init__(self, index: int) -> None:
            self._mapping = {
                "consultant_specialty": f"Specialty {index}",
                "decline_rate": 0.1,
            }

    class FakeResult:
        def fetchall(self):
            return [FakeRow(index) for index in range(60)]

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, parameters):
            return FakeResult()

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr(
        "app.execution.postgres.create_engine",
        lambda url: FakeEngine(),
    )

    result = execute_postgres_query(build_result, "postgresql+psycopg://readonly")

    assert result.row_count == 50
    assert len(result.rows) == 50


def test_execution_factory_uses_postgres_backend(monkeypatch, health_uk_catalogue) -> None:
    captured = {}
    build_result = build_query(
        health_uk_catalogue,
        AnalyticsRequest(
            metric_id="paid_claims",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
        ),
    )
    settings = Settings(
        execution_backend="postgres",
        readonly_database_url="postgresql+psycopg://readonly",
    )

    def fake_execute_postgres_query(build_result_arg, database_url):
        captured["build_result"] = build_result_arg
        captured["database_url"] = database_url
        return "postgres-result"

    monkeypatch.setattr(
        "app.execution.factory.execute_postgres_query",
        fake_execute_postgres_query,
    )

    result = execute_query(build_result, settings)

    assert result == "postgres-result"
    assert captured["build_result"] is build_result
    assert captured["database_url"] == "postgresql+psycopg://readonly"
