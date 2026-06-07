from pathlib import Path

from app.semantic.catalogue import load_catalogue, supported_dimensions, synonym_collisions


def test_health_uk_catalogue_loads_first_metric() -> None:
    catalogue_root = Path(__file__).resolve().parents[2] / "catalogues"

    catalogue = load_catalogue(catalogue_root, "health-uk")

    assert catalogue.name == "health-uk"
    assert set(catalogue.tables) == {
        "claims",
        "claim_lines",
        "claim_status_history",
        "declines",
        "enrolment_months",
        "members",
        "plans",
        "premium",
        "providers",
        "reserves",
    }
    assert set(catalogue.metrics) == {
        "case_reserves",
        "claim_count",
        "claim_frequency",
        "claim_severity",
        "covered_members",
        "decline_rate",
        "incurred_claims",
        "loss_ratio",
        "open_claim_rate",
        "out_of_network_rate",
        "paid_claims",
        "premium_per_member",
    }
    assert catalogue.metrics["loss_ratio"].time_anchor == "claims.incurred_date"
    assert catalogue.joins[0].left_table == "members"


def test_catalogue_inspection_helpers_match_makefile_targets() -> None:
    catalogue_root = Path(__file__).resolve().parents[2] / "catalogues"
    catalogue = load_catalogue(catalogue_root, "health-uk")

    assert supported_dimensions(catalogue) == [
        "consultant_specialty",
        "diagnosis_category",
        "month",
        "plan_tier",
        "region",
    ]
    assert synonym_collisions(catalogue) == {}
