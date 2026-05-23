from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


GOLDEN_FILE = Path(__file__).with_name("questions.yaml")


def test_golden_questions_match_contract(tmp_path) -> None:
    """Run approved product questions through the ask endpoint."""
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        questions = _load_golden_questions()
        responses = [
            TestClient(app).post("/ask", json=_request_payload(question))
            for question in questions
        ]
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    for question, response in zip(questions, responses, strict=True):
        assert response.status_code == 200, question["id"]
        _assert_expected_response(question, response.json())


def _load_golden_questions() -> list[dict[str, object]]:
    payload = yaml.safe_load(GOLDEN_FILE.read_text(encoding="utf-8"))
    return list(payload["questions"])


def _request_payload(question: dict[str, object]) -> dict[str, object]:
    payload = {"question": question["question"]}
    for field in ("start_date", "end_date", "plan_tier", "group_by"):
        if field in question:
            payload[field] = question[field]
    return payload


def _assert_expected_response(
    question: dict[str, object],
    body: dict[str, object],
) -> None:
    expected = question["expects"]
    assert isinstance(expected, dict)
    assert body["status"] == expected["status"], question["id"]

    if body["status"] == "answer":
        _assert_answer(question, body, expected)
    elif body["status"] == "clarification_required":
        _assert_clarification(question, body, expected)
    elif body["status"] == "blocked":
        assert body["safety"]["rule_id"] == expected["rule_id"], question["id"]
    elif body["status"] == "out_of_scope":
        assert body["scope"]["reason_id"] == expected["reason_id"], question["id"]


def _assert_answer(
    question: dict[str, object],
    body: dict[str, object],
    expected: dict[str, object],
) -> None:
    answer = body["answer"]
    assert answer["metric_id"] == expected["metric_id"], question["id"]

    if "row_count" in expected:
        assert answer["row_count"] == expected["row_count"], question["id"]
    if "min_row_count" in expected:
        assert answer["row_count"] >= expected["min_row_count"], question["id"]
    if "group_by" in expected:
        assert body["resolved_request"]["group_by"] == expected["group_by"], question["id"]

    result_columns = expected.get("result_columns", [])
    first_row = answer["rows"][0]
    for column in result_columns:
        assert column in first_row, question["id"]


def _assert_clarification(
    question: dict[str, object],
    body: dict[str, object],
    expected: dict[str, object],
) -> None:
    candidate_ids = [candidate["metric_id"] for candidate in body["candidates"]]
    assert candidate_ids == expected["candidate_metric_ids"], question["id"]
