from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AskExample:
    """One demo-ready question with its expected ask state."""

    id: str
    label: str
    question: str
    expected_status: str
    start_date: date | None = None
    end_date: date | None = None
    plan_tier: str | None = None
    group_by: tuple[str, ...] = ()


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
        id="answer_claim_frequency_plan_tier",
        label="Claim frequency by plan tier filter",
        question="Show claim frequency for the Comprehensive plan tier.",
        expected_status="answer",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    ),
    AskExample(
        id="answer_incurred_claims_plan_tier",
        label="Incurred claims by plan tier filter",
        question="Show incurred claims for the Comprehensive plan tier.",
        expected_status="answer",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    ),
    AskExample(
        id="answer_claim_severity_plan_tier",
        label="Claim severity by plan tier filter",
        question="Show claim severity for the Comprehensive plan tier.",
        expected_status="answer",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    ),
    AskExample(
        id="answer_decline_rate_q1",
        label="Decline rate in Q1",
        question="What was decline rate for the Comprehensive plan tier in Q1 2026?",
        expected_status="answer",
    ),
    AskExample(
        id="answer_decline_rate_by_specialty",
        label="Decline rate by specialty",
        question=(
            "What was decline rate by consultant specialty for the "
            "Comprehensive plan tier in Q1 2026?"
        ),
        expected_status="answer",
    ),
    AskExample(
        id="answer_loss_ratio_by_plan_tier",
        label="Loss ratio by plan tier",
        question="Show loss ratio by plan tier in Q1 2026.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_paid_claims_by_region",
        label="Paid claims by region",
        question="Show paid claims by region for the last six months.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_loss_ratio_by_month",
        label="Loss ratio by month",
        question="Show loss ratio by month in Q1 2026.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_paid_claims_by_diagnosis",
        label="Paid claims by diagnosis",
        question="Show paid claims by diagnosis category in Q1 2026.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_claim_frequency_ytd",
        label="Claim frequency YTD",
        question="Show claim frequency year to date.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_claim_count_q1",
        label="Claim count in Q1",
        question="Show claim count in Q1 2026.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_covered_members_q1",
        label="Covered members in Q1",
        question="Show covered members in Q1 2026.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_open_claim_rate_q4",
        label="Open claim rate in Q4",
        question="Show open claim rate in Q4 2025.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_out_of_network_rate_q1",
        label="Out-of-network rate",
        question="Show out of network rate for the Comprehensive plan tier in Q1 2026.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_premium_per_member_q1",
        label="Premium per member",
        question="Show premium per member in Q1 2026.",
        expected_status="answer",
    ),
    AskExample(
        id="answer_case_reserves_q4",
        label="Case reserves in Q4",
        question="Show case reserves in Q4 2025.",
        expected_status="answer",
    ),
    AskExample(
        id="date_required_loss_ratio",
        label="Date range required",
        question="What was loss ratio for the Comprehensive plan tier?",
        expected_status="date_range_required",
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
