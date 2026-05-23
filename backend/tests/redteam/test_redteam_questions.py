from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.main import app


QUESTIONS_FILE = Path(__file__).with_name("questions.yaml")


def test_redteam_questions_are_blocked() -> None:
    """Run unsafe user questions through the product ask endpoint."""
    cases = _load_cases(QUESTIONS_FILE, key="questions")

    for case in cases:
        response = TestClient(app).post("/ask", json={"question": case["question"]})
        body = response.json()

        assert response.status_code == 200, case["id"]
        assert body["status"] == "blocked", case["id"]
        assert body["resolved_request"] is None, case["id"]
        assert body["answer"] is None, case["id"]
        assert body["safety"]["rule_id"] == case["expected_rule_id"], case["id"]


def _load_cases(path: Path, key: str) -> list[dict[str, object]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(payload[key])
