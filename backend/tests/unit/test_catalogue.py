from pathlib import Path

from app.semantic.catalogue import load_catalogue


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
        "claim_frequency",
        "claim_severity",
        "decline_rate",
        "incurred_claims",
        "loss_ratio",
        "paid_claims",
    }
    assert catalogue.metrics["loss_ratio"].time_anchor == "claims.incurred_date"
    assert catalogue.joins[0].left_table == "members"
