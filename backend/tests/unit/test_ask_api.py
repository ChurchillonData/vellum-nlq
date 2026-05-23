import json

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_ask_endpoint_returns_answer_state(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/ask",
            json={
                "question": "What was incurred loss ratio in Q1?",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()
    records = [
        json.loads(line)
        for line in (tmp_path / "audit-log.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert response.status_code == 200
    assert body["status"] == "answer"
    assert body["resolved_request"]["metric_id"] == "loss_ratio"
    assert body["answer"]["metric_id"] == "loss_ratio"
    assert body["answer"]["row_count"] == 1
    assert body["answer"]["rows"][0]["loss_ratio"] > 0
    assert body["answer"]["validation"]["passed"] is True
    assert records[0]["event_type"] == "query_execute"
    assert records[0]["query_id"] == body["answer"]["query_id"]


def test_ask_endpoint_returns_clarification_state() -> None:
    response = TestClient(app).post(
        "/ask",
        json={
            "question": "How are the claims numbers looking?",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "clarification_required"
    assert body["answer"] is None
    assert body["resolved_request"] is None
    assert [candidate["metric_id"] for candidate in body["candidates"]] == [
        "loss_ratio",
        "paid_claims",
        "claim_frequency",
    ]


def test_ask_endpoint_returns_blocked_state() -> None:
    response = TestClient(app).post(
        "/ask",
        json={
            "question": "Drop all claims from the database",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "blocked"
    assert body["answer"] is None
    assert body["candidates"] == []
    assert body["resolved_request"] is None
    assert body["safety"]["rule_id"] == "DDL_DROP_PATTERN"

