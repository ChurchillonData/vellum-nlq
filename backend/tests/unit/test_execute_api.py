import json

from fastapi.testclient import TestClient

from app.config import get_settings
from app.execution.models import ExecutionDatasetSummary, ExecutionResult
from app.main import app


def test_execute_endpoint_runs_loss_ratio_against_demo_data(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "loss_ratio",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["query_id"].startswith("q_")
    assert body["execution_mode"] == "local_demo"
    assert body["metric_id"] == "loss_ratio"
    assert "%(start_date)s" in body["compact_sql"]
    assert "WITH claim_totals AS" not in body["compact_sql"]
    assert body["latency"]["planning_ms"] >= 0
    assert body["latency"]["execution_ms"] >= 0
    assert body["latency"]["total_ms"] >= body["latency"]["planning_ms"]
    assert body["row_count"] == 1
    assert body["rows"][0]["loss_ratio"] > 0
    assert body["dataset"]["member_count"] == 120
    assert body["validation"]["passed"] is True
    assert "Comprehensive plan tier loss ratio" in body["answer"]


def test_execute_endpoint_runs_paid_claims_against_demo_data(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "paid_claims",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "paid_claims"
    assert body["row_count"] == 1
    assert body["rows"][0]["paid_claims"] > 0
    assert body["validation"]["passed"] is True
    assert "Comprehensive plan tier paid claims" in body["answer"]


def test_execute_endpoint_runs_incurred_claims_against_demo_data(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "incurred_claims",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "incurred_claims"
    assert body["row_count"] == 1
    assert body["rows"][0]["incurred_claims"] > 0
    assert body["provenance"]["result_shape"]["max_rows"] == 1
    assert body["validation"]["passed"] is True
    assert "Comprehensive plan tier incurred claims" in body["answer"]


def test_execute_endpoint_runs_claim_frequency_against_demo_data(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "claim_frequency",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "claim_frequency"
    assert body["row_count"] == 1
    assert body["rows"][0]["claim_frequency"] > 0
    assert body["validation"]["passed"] is True
    assert "Comprehensive plan tier claim frequency" in body["answer"]


def test_execute_endpoint_runs_claim_severity_against_demo_data(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "claim_severity",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "claim_severity"
    assert body["row_count"] == 1
    assert body["rows"][0]["claim_severity"] > 0
    assert body["provenance"]["result_shape"]["max_rows"] == 1
    assert body["validation"]["passed"] is True
    assert "Comprehensive plan tier claim severity" in body["answer"]


def test_execute_endpoint_runs_decline_rate_against_demo_data(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "decline_rate",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "decline_rate"
    assert body["row_count"] == 1
    assert body["rows"][0]["decline_rate"] >= 0
    assert body["validation"]["passed"] is True
    assert "Comprehensive plan tier decline rate" in body["answer"]


def test_execute_endpoint_runs_decline_rate_grouped_by_specialty(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "decline_rate",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "group_by": ["consultant_specialty"],
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "decline_rate"
    assert body["row_count"] > 1
    assert "consultant_specialty" in body["rows"][0]
    assert body["provenance"]["result_shape"] == {
        "columns": ["consultant_specialty", "decline_rate"],
        "grain": "consultant_specialty",
        "max_rows": 50,
    }
    assert body["row_count"] <= 50
    assert "by consultant specialty" in body["answer"]


def test_execute_endpoint_runs_loss_ratio_grouped_by_month(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "loss_ratio",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "group_by": ["month"],
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "loss_ratio"
    assert body["row_count"] > 1
    assert "month" in body["rows"][0]
    assert body["provenance"]["result_shape"] == {
        "columns": ["month", "loss_ratio"],
        "grain": "month",
        "max_rows": 50,
    }
    assert body["validation"]["passed"] is True
    assert "by month" in body["answer"]


def test_execute_endpoint_runs_paid_claims_grouped_by_diagnosis_category(
    tmp_path,
) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "paid_claims",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "group_by": ["diagnosis_category"],
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "paid_claims"
    assert body["row_count"] > 1
    assert "diagnosis_category" in body["rows"][0]
    assert body["provenance"]["result_shape"] == {
        "columns": ["diagnosis_category", "paid_claims"],
        "grain": "diagnosis_category",
        "max_rows": 50,
    }
    assert body["validation"]["passed"] is True
    assert "by diagnosis category" in body["answer"]


def test_execute_endpoint_writes_execution_audit_event(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "loss_ratio",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    records = [
        json.loads(line)
        for line in (tmp_path / "audit-log.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert response.status_code == 200
    assert records[0]["query_id"] == response.json()["query_id"]
    assert records[0]["event_type"] == "query_execute"
    assert records[0]["execution"]["mode"] == "local_demo"
    assert records[0]["execution"]["row_count"] == 1


def test_execute_endpoint_uses_configured_postgres_backend(monkeypatch, tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_backend = settings.execution_backend
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.execution_backend = "postgres"

    def fake_execute_configured_query(build_result, settings_arg):
        assert settings_arg.execution_backend == "postgres"
        return ExecutionResult(
            rows=[{"paid_claims": 1234.56}],
            row_count=1,
            answer="Paid claims from Postgres.",
            dataset=ExecutionDatasetSummary(
                name="health-uk postgres",
                member_count=None,
                claim_count=None,
                premium_row_count=None,
            ),
            mode="postgres",
        )

    monkeypatch.setattr(
        "app.api.routes.execute_configured_query",
        fake_execute_configured_query,
    )

    try:
        response = TestClient(app).post(
            "/queries/execute",
            json={
                "metric_id": "paid_claims",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.execution_backend = original_backend

    body = response.json()
    records = [
        json.loads(line)
        for line in (tmp_path / "audit-log.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert response.status_code == 200
    assert body["execution_mode"] == "postgres"
    assert body["dataset"]["name"] == "health-uk postgres"
    assert body["dataset"]["member_count"] is None
    assert records[0]["execution"]["mode"] == "postgres"


def test_execute_endpoint_reports_unknown_metric() -> None:
    response = TestClient(app).post(
        "/queries/execute",
        json={
            "metric_id": "not_a_metric",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "unknown metric: not_a_metric"}
