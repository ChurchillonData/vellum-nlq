import json

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_preview_endpoint_writes_audit_event(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    settings.audit_log_path = tmp_path / "audit-log.jsonl"

    try:
        response = TestClient(app).post(
            "/queries/preview",
            json={
                "metric_id": "loss_ratio",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path

    body = response.json()
    records = [
        json.loads(line)
        for line in (tmp_path / "audit-log.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert response.status_code == 200
    assert body["query_id"].startswith("q_")
    assert records[0]["query_id"] == body["query_id"]
    assert records[0]["validation"]["passed"] is True


def test_query_lookup_endpoint_returns_audit_event(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    settings.audit_log_path = tmp_path / "audit-log.jsonl"

    try:
        client = TestClient(app)
        preview_response = client.post(
            "/queries/preview",
            json={
                "metric_id": "loss_ratio",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
        query_id = preview_response.json()["query_id"]

        lookup_response = client.get(f"/queries/{query_id}")
    finally:
        settings.audit_log_path = original_path

    body = lookup_response.json()

    assert lookup_response.status_code == 200
    assert body["query_id"] == query_id
    assert body["event_type"] == "query_preview"
    assert body["metric_id"] == "loss_ratio"
    assert body["provenance"]["time_anchor"] == "claims.incurred_date"


def test_query_lookup_endpoint_reports_missing_query(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    settings.audit_log_path = tmp_path / "audit-log.jsonl"

    try:
        response = TestClient(app).get("/queries/q_missing")
    finally:
        settings.audit_log_path = original_path

    assert response.status_code == 404
    assert response.json() == {"detail": "query not found: q_missing"}


def test_preview_endpoint_returns_loss_ratio_sql_and_provenance() -> None:
    response = TestClient(app).post(
        "/queries/preview",
        json={
            "metric_id": "loss_ratio",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "plan_tier": "Comprehensive",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["query_id"].startswith("q_")
    assert body["metric_id"] == "loss_ratio"
    assert "%(start_date)s" in body["sql"]
    assert "Comprehensive" not in body["sql"]
    assert body["parameters"]["plan_tier"] == "Comprehensive"
    assert body["provenance"]["time_anchor"] == "claims.incurred_date"
    assert body["provenance"]["result_shape"] == {
        "columns": ["loss_ratio"],
        "grain": "single_metric",
    }
    assert body["validation"]["passed"] is True
    assert "select_only" in body["validation"]["rules_checked"]


def test_preview_endpoint_reports_unknown_metric() -> None:
    response = TestClient(app).post(
        "/queries/preview",
        json={
            "metric_id": "not_a_metric",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "unknown metric: not_a_metric"}


def test_preview_endpoint_rejects_reverse_date_range() -> None:
    response = TestClient(app).post(
        "/queries/preview",
        json={
            "metric_id": "loss_ratio",
            "start_date": "2026-03-31",
            "end_date": "2026-01-01",
        },
    )

    assert response.status_code == 422
