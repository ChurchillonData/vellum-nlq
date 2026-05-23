from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AskExample:
    """One demo-ready question with its expected ask state."""

    id: str
    label: str
    question: str
    expected_status: str
    start_date: date
    end_date: date
    plan_tier: str | None = None


GOLDEN_ASK_EXAMPLES = (
    AskExample(
        id="answer_loss_ratio_q1",
        label="Loss ratio in Q1",
        question="What was incurred loss ratio in Q1?",
        expected_status="answer",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    ),
    AskExample(
        id="answer_paid_claims_plan_tier",
        label="Paid claims by plan tier filter",
        question="Show paid claims for the Comprehensive plan tier.",
        expected_status="answer",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    ),
    AskExample(
        id="answer_incurred_loss_ratio_period",
        label="Incurred loss ratio with explicit period",
        question="What is the incurred loss ratio for Comprehensive from January to March 2026?",
        expected_status="answer",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    ),
    AskExample(
        id="clarify_claims_numbers",
        label="Ambiguous claims numbers",
        question="How are the claims numbers looking?",
        expected_status="clarification_required",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    AskExample(
        id="clarify_claims_performance",
        label="Ambiguous claims performance",
        question="Show me claims performance.",
        expected_status="clarification_required",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    AskExample(
        id="clarify_claims_happening",
        label="Ambiguous claims trend wording",
        question="What is happening with claims?",
        expected_status="clarification_required",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    AskExample(
        id="blocked_drop_claims",
        label="Blocked DROP intent",
        question="Drop all claims from the database.",
        expected_status="blocked",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    AskExample(
        id="blocked_delete_premium",
        label="Blocked DELETE intent",
        question="Delete all premium records.",
        expected_status="blocked",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    AskExample(
        id="blocked_update_claims",
        label="Blocked UPDATE intent",
        question="Update every claim status to closed.",
        expected_status="blocked",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    AskExample(
        id="out_of_scope_loss_ratio_forecast",
        label="Out-of-scope forecast",
        question="What will loss ratio be next quarter?",
        expected_status="out_of_scope",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    AskExample(
        id="out_of_scope_claims_prediction",
        label="Out-of-scope claims prediction",
        question="Predict paid claims for Q2.",
        expected_status="out_of_scope",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
    AskExample(
        id="out_of_scope_future_projection",
        label="Out-of-scope future projection",
        question="Forecast claim frequency next month.",
        expected_status="out_of_scope",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    ),
)
