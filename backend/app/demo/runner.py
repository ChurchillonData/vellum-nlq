from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


@dataclass(frozen=True)
class DemoStep:
    """One question in the guided Vellum-NLQ demo."""

    label: str
    question: str
    expected_status: str
    start_date: date | None = None
    end_date: date | None = None


SCRIPTED_STEPS = (
    DemoStep(
        label="Happy path answer",
        question="What was loss ratio for the Comprehensive plan tier in Q1 2026?",
        expected_status="answer",
    ),
    DemoStep(
        label="Grouped analytics",
        question=(
            "What was decline rate by consultant specialty for the "
            "Comprehensive plan tier in Q1 2026?"
        ),
        expected_status="answer",
    ),
    DemoStep(
        label="Clarification before guessing",
        question="How are the claims numbers looking?",
        expected_status="clarification_required",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    DemoStep(
        label="Out-of-scope refusal",
        question="What will loss ratio be next quarter?",
        expected_status="out_of_scope",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    DemoStep(
        label="Safety rejection",
        question="Drop all claims from the database.",
        expected_status="blocked",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
)


def run_demo(steps: Sequence[DemoStep] = SCRIPTED_STEPS) -> int:
    """Run the guided demo through the product-facing ask endpoint."""
    client = TestClient(app)
    failed = False

    print("Vellum-NLQ scripted demo")
    print("Controlled NLQ for governed UK PMI claims analytics")
    print("")

    for index, step in enumerate(steps, start=1):
        response = client.post("/ask", json=_request_payload(step))
        body = response.json()
        status = body.get("status")
        passed = response.status_code == 200 and status == step.expected_status
        failed = failed or not passed

        print(f"{index}. {step.label}")
        print(f"   Question: {step.question}")
        print(f"   Status:   {status} ({'OK' if passed else 'CHECK'})")
        _print_state_details(body)
        print("")

    if failed:
        print("Demo finished with contract mismatches.")
        return 1

    print("Demo finished successfully.")
    return 0


def _request_payload(step: DemoStep) -> dict[str, Any]:
    """Build the JSON request for one demo step."""
    payload: dict[str, Any] = {"question": step.question}
    if step.start_date is not None:
        payload["start_date"] = step.start_date.isoformat()
    if step.end_date is not None:
        payload["end_date"] = step.end_date.isoformat()
    return payload


def _print_state_details(body: dict[str, Any]) -> None:
    """Print concise details for the returned ask state."""
    status = body.get("status")

    if status == "answer":
        answer = body["answer"]
        validation = answer["validation"]
        provenance = answer["provenance"]
        print(f"   Metric:   {answer['metric_id']} ({provenance['metric_version']})")
        print(f"   Answer:   {answer['answer']}")
        print(f"   Rows:     {answer['row_count']} via {answer['execution_mode']}")
        print(
            "   Guard:    "
            f"{'passed' if validation['passed'] else 'failed'} "
            f"({len(validation['rules_checked'])} rules)"
        )
        print(f"   Query ID: {answer['query_id']}")
        return

    if status == "clarification_required":
        candidates = ", ".join(
            candidate["metric_id"] for candidate in body.get("candidates", [])
        )
        print(f"   Message:  {body['message']}")
        print(f"   Options:  {candidates}")
        print(f"   Query ID: {body['query_id']}")
        return

    if status == "blocked":
        safety = body.get("safety") or {}
        print(f"   Rule:     {safety.get('rule_id')}")
        print(f"   Reason:   {safety.get('reason')}")
        print(f"   Query ID: {body['query_id']}")
        return

    if status == "out_of_scope":
        scope = body.get("scope") or {}
        print(f"   Reason:   {scope.get('reason')}")
        print(f"   Query ID: {body['query_id']}")
        return

    print(f"   Message:  {body.get('message')}")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for the guided demo."""
    parser = argparse.ArgumentParser(description="Run the Vellum-NLQ demo script.")
    parser.parse_args(argv)
    return run_demo()


if __name__ == "__main__":
    raise SystemExit(main())
