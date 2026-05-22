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
