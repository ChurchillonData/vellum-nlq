from datetime import date
from decimal import Decimal

import pytest

from app.seeds.synthetic import build_seed_data
from seeds.generate import (
    add_row_counts,
    chunk_ranges,
    count_seed_rows,
    empty_row_counts,
    resolve_seed_config,
)

AS_OF_DATE = date(2026, 6, 5)


def test_seed_data_builds_related_claims_rows() -> None:
    seed_data = build_seed_data(member_count=12, month_count=3, as_of_date=AS_OF_DATE)

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


def test_seed_data_supports_chunked_portfolio_generation() -> None:
    first_chunk = build_seed_data(
        member_count=10,
        month_count=3,
        as_of_date=AS_OF_DATE,
        start_member_index=0,
        include_reference_data=True,
    )
    second_chunk = build_seed_data(
        member_count=10,
        month_count=3,
        as_of_date=AS_OF_DATE,
        start_member_index=10,
        include_reference_data=False,
    )
    full_seed = build_seed_data(member_count=20, month_count=3, as_of_date=AS_OF_DATE)

    chunked_member_ids = {row["id"] for row in first_chunk.members + second_chunk.members}
    full_member_ids = {row["id"] for row in full_seed.members}

    assert chunked_member_ids == full_member_ids
    assert len(first_chunk.plans) == 3
    assert len(first_chunk.providers) == 4
    assert second_chunk.plans == []
    assert second_chunk.providers == []
    assert len(first_chunk.premium) + len(second_chunk.premium) == len(full_seed.premium)
    assert len(first_chunk.claims) + len(second_chunk.claims) == len(full_seed.claims)


def test_seed_cli_resolves_portfolio_profile_defaults() -> None:
    config = resolve_seed_config("portfolio")

    assert config.member_count == 200_000
    assert config.month_count == 18
    assert config.chunk_size == 10_000


def test_seed_cli_allows_safe_profile_overrides() -> None:
    config = resolve_seed_config(
        "portfolio",
        member_count=50_000,
        month_count=12,
        chunk_size=5_000,
    )

    assert config.member_count == 50_000
    assert config.month_count == 12
    assert config.chunk_size == 5_000


def test_seed_cli_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError, match="member_count"):
        resolve_seed_config("local", member_count=0)

    with pytest.raises(ValueError, match="month_count"):
        resolve_seed_config("local", month_count=0)

    with pytest.raises(ValueError, match="chunk_size"):
        resolve_seed_config("local", chunk_size=0)


def test_seed_cli_builds_chunk_plan() -> None:
    assert chunk_ranges(member_count=25, chunk_size=10) == [(0, 10), (10, 10), (20, 5)]


def test_seed_cli_reports_all_table_counts() -> None:
    seed_data = build_seed_data(member_count=12, month_count=3, as_of_date=AS_OF_DATE)
    totals = empty_row_counts()

    add_row_counts(totals, count_seed_rows(seed_data))

    assert totals["plans"] == 3
    assert totals["providers"] == 4
    assert totals["members"] == 12
    assert totals["enrolment_months"] == 36
    assert totals["premium"] == 36
    assert totals["claims"] == len(seed_data.claims)
    assert totals["claim_lines"] == len(seed_data.claim_lines)
    assert totals["claim_status_history"] == len(seed_data.claim_status_history)
    assert totals["reserves"] == len(seed_data.reserves)
    assert totals["declines"] == len(seed_data.declines)


def test_seed_data_supports_q1_comprehensive_loss_ratio_demo() -> None:
    seed_data = build_seed_data(
        member_count=2_000,
        month_count=18,
        as_of_date=AS_OF_DATE,
    )
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
    assert Decimal("0.78") <= claim_total / premium_total <= Decimal("0.92")
