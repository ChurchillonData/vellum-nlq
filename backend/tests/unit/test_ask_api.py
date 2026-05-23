import json
from datetime import date

from fastapi.testclient import TestClient

from app.config import get_settings
from app.intent.factory import set_intent_provider_override
from app.intent.fake import FakeIntentProvider
from app.intent.models import IntentResult
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
    assert body["query_id"].startswith("q_")
    assert body["answer"]["query_id"] == body["query_id"]
    assert records[0]["event_type"] == "ask"
    assert records[0]["status"] == "answer"
    assert records[0]["query_id"] == body["query_id"]


def test_ask_endpoint_infers_supported_filters_from_question(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/ask",
            json={
                "question": (
                    "What was loss ratio for the Comprehensive plan tier in Q1 2026?"
                ),
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "answer"
    assert body["resolved_request"]["metric_id"] == "loss_ratio"
    assert body["resolved_request"]["start_date"] == "2026-01-01"
    assert body["resolved_request"]["end_date"] == "2026-03-31"
    assert body["resolved_request"]["plan_tier"] == "Comprehensive"
    assert body["answer"]["parameters"]["plan_tier"] == "Comprehensive"


def test_ask_endpoint_infers_decline_rate_grouping(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        response = TestClient(app).post(
            "/ask",
            json={
                "question": (
                    "What was decline rate by consultant specialty for the "
                    "Comprehensive plan tier in Q1 2026?"
                ),
            },
        )
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "answer"
    assert body["resolved_request"]["metric_id"] == "decline_rate"
    assert body["resolved_request"]["group_by"] == ["consultant_specialty"]
    assert body["answer"]["row_count"] >= 1
    assert body["answer"]["provenance"]["result_shape"] == {
        "columns": ["consultant_specialty", "decline_rate"],
        "grain": "consultant_specialty",
        "max_rows": 50,
    }


def test_ask_endpoint_uses_provider_intent_without_provider_sql(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120
    set_intent_provider_override(
        FakeIntentProvider(
            IntentResult(
                metric_id="claim_severity",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
                plan_tier="Comprehensive",
                confidence=0.91,
                source="fake",
            )
        )
    )

    try:
        response = TestClient(app).post(
            "/ask",
            json={"question": "How expensive were closed claims?"},
        )
    finally:
        set_intent_provider_override(None)
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    body = response.json()
    records = [
        json.loads(line)
        for line in (tmp_path / "audit-log.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert response.status_code == 200
    assert body["status"] == "answer"
    assert body["resolved_request"]["metric_id"] == "claim_severity"
    assert body["answer"]["metric_id"] == "claim_severity"
    assert "claim_severity" in body["answer"]["sql"]
    assert body["answer"]["validation"]["passed"] is True
    assert records[0]["request"]["metric_id"] == "claim_severity"


def test_ask_endpoint_rejects_provider_metric_outside_catalogue(tmp_path) -> None:
    response, records = _post_ask_with_audit(
        tmp_path,
        {"question": "How expensive were closed claims?"},
        provider=FakeIntentProvider(
            IntentResult(
                metric_id="not_a_catalogue_metric",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
                source="fake",
            )
        ),
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "unresolved"
    assert body["answer"] is None
    assert body["resolved_request"] is None
    assert records[0]["status"] == "unresolved"
    assert records[0]["sql"] is None


def test_ask_endpoint_blocks_unsafe_question_before_provider_intent(tmp_path) -> None:
    response, records = _post_ask_with_audit(
        tmp_path,
        {"question": "Drop all claims from the database"},
        provider=FakeIntentProvider(
            IntentResult(
                metric_id="loss_ratio",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
                source="fake",
            )
        ),
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "blocked"
    assert body["safety"]["rule_id"] == "DDL_DROP_PATTERN"
    assert records[0]["status"] == "blocked"
    assert records[0]["sql"] is None


def test_ask_endpoint_requires_date_range_for_answerable_question(tmp_path) -> None:
    response, records = _post_ask_with_audit(
        tmp_path,
        {"question": "What was loss ratio for the Comprehensive plan tier?"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "date_range_required"
    assert body["answer"] is None
    assert body["resolved_request"] is None
    assert "date range" in body["message"]
    assert body["query_id"] == records[0]["query_id"]
    assert records[0]["event_type"] == "ask"
    assert records[0]["status"] == "date_range_required"
    assert records[0]["sql"] is None


def test_ask_endpoint_blocks_unsafe_question_without_dates(tmp_path) -> None:
    response, records = _post_ask_with_audit(
        tmp_path,
        {"question": "Drop all claims from the database"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "blocked"
    assert body["safety"]["rule_id"] == "DDL_DROP_PATTERN"
    assert body["query_id"] == records[0]["query_id"]
    assert records[0]["status"] == "blocked"
    assert records[0]["safety"]["rule_id"] == "DDL_DROP_PATTERN"


def test_ask_examples_endpoint_returns_examples_per_state() -> None:
    response = TestClient(app).get("/ask/examples")

    body = response.json()
    statuses = [example["expected_status"] for example in body["examples"]]

    assert response.status_code == 200
    assert len(body["examples"]) == 17
    assert statuses.count("answer") == 7
    assert statuses.count("date_range_required") == 1
    assert statuses.count("clarification_required") == 3
    assert statuses.count("blocked") == 3
    assert statuses.count("out_of_scope") == 3


def test_every_golden_ask_example_returns_expected_state(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    original_member_count = settings.demo_member_count
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    settings.demo_member_count = 120

    try:
        examples = TestClient(app).get("/ask/examples").json()["examples"]
        responses = [
            TestClient(app).post(
                "/ask",
                json={
                    "question": example["question"],
                    "start_date": example["start_date"],
                    "end_date": example["end_date"],
                    "plan_tier": example["plan_tier"],
                },
            )
            for example in examples
        ]
    finally:
        settings.audit_log_path = original_path
        settings.demo_member_count = original_member_count

    for example, response in zip(examples, responses, strict=True):
        assert response.status_code == 200
        assert response.json()["status"] == example["expected_status"]


def test_ask_endpoint_returns_clarification_state(tmp_path) -> None:
    response, records = _post_ask_with_audit(
        tmp_path,
        {
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
    assert body["query_id"] == records[0]["query_id"]
    assert records[0]["status"] == "clarification_required"
    assert records[0]["candidates"][0]["metric_id"] == "loss_ratio"
    assert records[0]["sql"] is None


def test_ask_endpoint_returns_blocked_state(tmp_path) -> None:
    response, records = _post_ask_with_audit(
        tmp_path,
        {
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
    assert body["query_id"] == records[0]["query_id"]
    assert records[0]["status"] == "blocked"
    assert records[0]["safety"]["severity"] == "critical"


def test_ask_endpoint_returns_out_of_scope_state(tmp_path) -> None:
    response, records = _post_ask_with_audit(
        tmp_path,
        {
            "question": "What will loss ratio be next quarter?",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "out_of_scope"
    assert body["answer"] is None
    assert body["candidates"] == []
    assert body["resolved_request"] is None
    assert body["scope"]["reason_id"] == "forecasting_not_supported"
    assert body["query_id"] == records[0]["query_id"]
    assert records[0]["status"] == "out_of_scope"
    assert records[0]["scope"]["reason_id"] == "forecasting_not_supported"


def test_ask_audit_record_can_be_loaded_by_query_id(tmp_path) -> None:
    settings = get_settings()
    original_path = settings.audit_log_path
    settings.audit_log_path = tmp_path / "audit-log.jsonl"

    try:
        response = TestClient(app).post(
            "/ask",
            json={"question": "Drop all claims from the database"},
        )
        body = response.json()
        lookup = TestClient(app).get(f"/queries/{body['query_id']}")
    finally:
        settings.audit_log_path = original_path

    assert lookup.status_code == 200
    assert lookup.json()["query_id"] == body["query_id"]
    assert lookup.json()["status"] == "blocked"


def _post_ask_with_audit(
    tmp_path,
    payload: dict[str, object],
    provider: object | None = None,
) -> tuple[object, list[dict[str, object]]]:
    settings = get_settings()
    original_path = settings.audit_log_path
    settings.audit_log_path = tmp_path / "audit-log.jsonl"
    set_intent_provider_override(provider)

    try:
        response = TestClient(app).post("/ask", json=payload)
        records = [
            json.loads(line)
            for line in settings.audit_log_path.read_text(encoding="utf-8").splitlines()
        ]
    finally:
        set_intent_provider_override(None)
        settings.audit_log_path = original_path

    return response, records
