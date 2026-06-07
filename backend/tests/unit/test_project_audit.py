from pathlib import Path

from app.ask.examples import GOLDEN_ASK_EXAMPLES
from app.planner.grouping import supported_groupings_for_metric
from app.sql.guard_catalogue import ALLOWED_FUNCTIONS


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_project_contract_documents_current_example_count() -> None:
    """Keep public docs aligned with the backend demo example contract."""
    example_ids = [example.id for example in GOLDEN_ASK_EXAMPLES]
    assert len(example_ids) == len(set(example_ids))
    assert len(example_ids) == 28

    docs = _read("README.md") + _read("docs/BUILD_PLAN.md") + _read("docs/api-contract.md")
    assert "twenty-six" not in docs.casefold()
    assert "Twenty-six" not in docs
    assert "twenty-eight" in docs.casefold()


def test_project_contract_documents_current_groupings() -> None:
    """Keep docs aligned with the deterministic grouped analytics surface."""
    loss_ratio_groupings = supported_groupings_for_metric("loss_ratio")
    paid_claims_groupings = supported_groupings_for_metric("paid_claims")
    decline_rate_groupings = supported_groupings_for_metric("decline_rate")

    assert loss_ratio_groupings == ["month", "plan_tier", "region"]
    assert paid_claims_groupings == [
        "diagnosis_category",
        "month",
        "plan_tier",
        "region",
    ]
    assert decline_rate_groupings == [
        "consultant_specialty",
        "diagnosis_category",
        "month",
        "plan_tier",
        "region",
    ]

    api_contract = _read("docs/api-contract.md")
    assert '`by month`' in api_contract
    assert '`by diagnosis category`' in api_contract
    assert '"allowed_dimensions": ["month", "plan_tier", "region"]' in api_contract


def test_project_contract_documents_current_function_allowlist() -> None:
    """Keep the safety documentation aligned with the SQL guard allowlist."""
    assert ALLOWED_FUNCTIONS == {
        "CAST",
        "COUNT",
        "DATE_TRUNC",
        "NULLIF",
        "SUM",
        "TIMESTAMP_TRUNC",
    }

    safety_docs = _read("README.md") + _read("docs/safety-model.md")
    for function_name in sorted(ALLOWED_FUNCTIONS):
        assert f"`{function_name}`" in safety_docs


def test_frontend_exposes_new_grouped_examples_as_quick_controls() -> None:
    """Keep the Ask page discovery controls aligned with backend examples."""
    ask_workspace = _read("frontend/src/components/AskWorkspace.tsx")

    assert "answer_loss_ratio_by_month" in ask_workspace
    assert "answer_paid_claims_by_diagnosis" in ask_workspace
    assert "loss ratio by month" in ask_workspace
    assert "paid claims by diagnosis" in ask_workspace


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")
