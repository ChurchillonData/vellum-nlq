import json
from datetime import date

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest
from app.api.schemas import QueryPreviewRequest
from app.ask.service import AskRequest, answer_question
from app.audit.logger import (
    build_ask_audit_event,
    build_preview_audit_event,
)
from app.audit.store import JsonlAuditStore, PostgresAuditStore, build_audit_store
from app.config import Settings, get_settings


def test_jsonl_audit_logger_records_preview_event(tmp_path, health_uk_catalogue) -> None:
    request = QueryPreviewRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )
    build_result = build_query(
        health_uk_catalogue,
        AnalyticsRequest.model_validate(request),
    )
    event = build_preview_audit_event(request, build_result)
    log_path = tmp_path / "audit-log.jsonl"

    JsonlAuditStore(log_path).record(event)

    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["query_id"].startswith("q_")
    assert record["event_type"] == "query_preview"
    assert record["request"]["start_date"] == "2026-01-01"
    assert record["metric_id"] == "loss_ratio"
    assert "%(start_date)s" in record["sql"]
    assert "%(start_date)s" in record["compact_sql"]
    assert "WITH claim_totals AS" not in record["compact_sql"]
    assert record["provenance"]["time_anchor"] == "claims.incurred_date"
    assert record["provenance"]["result_shape"] == {
        "columns": ["loss_ratio"],
        "grain": "single_metric",
        "max_rows": 1,
    }
    assert record["validation"]["passed"] is True
    assert "join_allowlist" in record["validation"]["rules_checked"]


def test_jsonl_audit_logger_finds_event_by_query_id(tmp_path, health_uk_catalogue) -> None:
    request = QueryPreviewRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )
    build_result = build_query(
        health_uk_catalogue,
        AnalyticsRequest.model_validate(request),
    )
    event = build_preview_audit_event(request, build_result)
    logger = JsonlAuditStore(tmp_path / "audit-log.jsonl")
    logger.record(event)

    record = logger.find_by_query_id(event.query_id)

    assert record is not None
    assert record["query_id"] == event.query_id
    assert record["metric_id"] == "loss_ratio"


def test_build_ask_audit_event_records_blocked_state(health_uk_catalogue) -> None:
    request = AskRequest(
        question="Drop all claims from the database",
        metric_id=None,
        start_date=None,
        end_date=None,
        plan_tier=None,
    )
    result = answer_question(
        health_uk_catalogue,
        request,
        settings=get_settings(),
    )

    event = build_ask_audit_event(request, result)

    assert event.query_id.startswith("q_")
    assert event.event_type == "ask"
    assert event.status == "blocked"
    assert event.request["question"] == "Drop all claims from the database"
    assert event.safety == {
        "rule_id": "DDL_DROP_PATTERN",
        "severity": "critical",
        "reason": "Question contains destructive DROP intent.",
    }
    assert event.sql is None
    assert event.provenance is None


def test_audit_store_defaults_to_jsonl(tmp_path) -> None:
    settings = Settings(audit_log_path=tmp_path / "audit-log.jsonl")

    store = build_audit_store(settings)

    assert isinstance(store, JsonlAuditStore)


def test_audit_store_can_use_postgres_backend(monkeypatch) -> None:
    captured = {}

    def fake_create_engine(url: str):
        captured["url"] = url
        return object()

    monkeypatch.setattr("app.audit.store.create_engine", fake_create_engine)

    settings = Settings(
        audit_backend="postgres",
        audit_database_url="postgresql+psycopg://audit-writer",
    )
    store = build_audit_store(settings)

    assert isinstance(store, PostgresAuditStore)
    assert captured["url"] == "postgresql+psycopg://audit-writer"


def test_postgres_audit_store_inserts_json_safe_payload(
    monkeypatch,
    health_uk_catalogue,
) -> None:
    request = QueryPreviewRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )
    build_result = build_query(
        health_uk_catalogue,
        AnalyticsRequest.model_validate(request),
    )
    event = build_preview_audit_event(request, build_result)
    captured = {}

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, _statement, parameters):
            captured["parameters"] = parameters
            return None

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    monkeypatch.setattr(
        "app.audit.store.create_engine",
        lambda _url: FakeEngine(),
    )

    PostgresAuditStore("postgresql+psycopg://audit-writer").record(event)

    parameters = captured["parameters"]
    assert parameters["query_id"] == event.query_id
    assert parameters["event_type"] == "query_preview"
    assert parameters["payload"]["request"]["start_date"] == "2026-01-01"
    assert parameters["payload"]["parameters"]["start_date"] == "2026-01-01"
