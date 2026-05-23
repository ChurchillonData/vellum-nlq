from datetime import date
from decimal import Decimal

from app.seeds.synthetic import build_seed_data


def test_seed_data_builds_related_claims_rows() -> None:
    seed_data = build_seed_data(member_count=12, month_count=3)

    member_ids = {row["id"] for row in seed_data.members}
    claim_ids = {row["id"] for row in seed_data.claims}
    claim_line_ids = {row["id"] for row in seed_data.claim_lines}

    assert len(seed_data.members) == 12
    assert len(seed_data.enrolment_months) == 36
    assert len(seed_data.premium) == 36
    assert seed_data.claims
    assert {row["member_id"] for row in seed_data.claims} <= member_ids
    assert {row["claim_id"] for row in seed_data.claim_lines} <= claim_ids
    assert {row["claim_line_id"] for row in seed_data.declines} <= claim_line_ids


def test_seed_data_supports_q1_comprehensive_loss_ratio_demo() -> None:
    seed_data = build_seed_data(member_count=120, month_count=18)
    plans = {row["id"]: row for row in seed_data.plans}
    members = {row["id"]: row for row in seed_data.members}
    start_date = date(2026, 1, 1)
    end_date = date(2026, 3, 31)

    claim_total = Decimal("0")
    premium_total = Decimal("0")

    for row in seed_data.claims:
        member = members[row["member_id"]]
        plan = plans[member["plan_id"]]
        if (
            start_date <= row["incurred_date"] <= end_date
            and plan["plan_tier"] == "Comprehensive"
        ):
            claim_total += row["net_incurred_amount"]

    for row in seed_data.premium:
        member = members[row["member_id"]]
        plan = plans[member["plan_id"]]
        if (
            start_date <= row["coverage_month"] <= end_date
            and plan["plan_tier"] == "Comprehensive"
        ):
            premium_total += row["earned_amount"]

    assert claim_total > 0
    assert premium_total > 0
