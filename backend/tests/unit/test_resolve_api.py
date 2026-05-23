from fastapi.testclient import TestClient

from app.main import app


def test_resolve_endpoint_returns_metric_for_specific_question() -> None:
    response = TestClient(app).post(
        "/queries/resolve",
        json={
            "question": "What was incurred loss ratio in Q1?",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "plan_tier": "Comprehensive",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "resolved"
    assert body["resolved_request"] == {
        "metric_id": "loss_ratio",
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
        "plan_tier": "Comprehensive",
    }
    assert body["candidates"][0]["metric_id"] == "loss_ratio"


def test_resolve_endpoint_returns_clarification_candidates() -> None:
    response = TestClient(app).post(
        "/queries/resolve",
        json={
            "question": "How are the claims numbers looking?",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "clarification_required"
    assert body["resolved_request"] is None
    assert [candidate["metric_id"] for candidate in body["candidates"]] == [
        "loss_ratio",
        "paid_claims",
        "claim_frequency",
    ]


def test_resolve_endpoint_rejects_reverse_date_range() -> None:
    response = TestClient(app).post(
        "/queries/resolve",
        json={
            "question": "Show loss ratio",
            "start_date": "2026-03-31",
            "end_date": "2026-01-01",
        },
    )

    assert response.status_code == 422


def test_resolve_endpoint_blocks_destructive_database_intent() -> None:
    response = TestClient(app).post(
        "/queries/resolve",
        json={
            "question": "Drop all claims from the database",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "blocked"
    assert body["candidates"] == []
    assert body["resolved_request"] is None
    assert body["safety"] == {
        "rule_id": "DDL_DROP_PATTERN",
        "severity": "critical",
        "reason": "Question contains destructive DROP intent.",
    }
