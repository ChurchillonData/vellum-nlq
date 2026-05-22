import json
from datetime import date

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest
from app.api.schemas import QueryPreviewRequest
from app.audit.logger import JsonlAuditLogger, build_preview_audit_event


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

    JsonlAuditLogger(log_path).record(event)

    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["query_id"].startswith("q_")
    assert record["event_type"] == "query_preview"
    assert record["request"]["start_date"] == "2026-01-01"
    assert record["metric_id"] == "loss_ratio"
    assert "%(start_date)s" in record["sql"]
    assert record["provenance"]["time_anchor"] == "claims.incurred_date"
    assert record["provenance"]["result_shape"] == {
        "columns": ["loss_ratio"],
        "grain": "single_metric",
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
    logger = JsonlAuditLogger(tmp_path / "audit-log.jsonl")
    logger.record(event)

    record = logger.find_by_query_id(event.query_id)

    assert record is not None
    assert record["query_id"] == event.query_id
    assert record["metric_id"] == "loss_ratio"
