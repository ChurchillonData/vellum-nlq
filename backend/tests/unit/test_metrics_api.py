from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_returns_active_catalogue_metrics() -> None:
    response = TestClient(app).get("/metrics")

    body = response.json()
    metric_ids = [metric["id"] for metric in body["metrics"]]

    assert response.status_code == 200
    assert body["catalogue"] == "health-uk"
    assert metric_ids == sorted(metric_ids)
    assert metric_ids == [
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
    ]


def test_metrics_endpoint_exposes_loss_ratio_definition() -> None:
    response = TestClient(app).get("/metrics")

    loss_ratio = {
        metric["id"]: metric
        for metric in response.json()["metrics"]
    }["loss_ratio"]

    assert loss_ratio["label"] == "Loss ratio"
    assert loss_ratio["formula"]["numerator"] == "SUM(claims.net_incurred_amount)"
    assert loss_ratio["formula"]["denominator"] == "SUM(premium.earned_amount)"
    assert loss_ratio["time_anchor"] == "claims.incurred_date"
    assert loss_ratio["required_tables"] == ["claims", "premium"]
    assert loss_ratio["version"] == "Vellum 2.5"
    assert loss_ratio["allowed_dimensions"] == ["month", "plan_tier", "region"]
    assert "claims.member_id -> members.id (many_to_one)" in loss_ratio["join_preview"]
    assert "premium.member_id -> members.id (many_to_one)" in loss_ratio["join_preview"]


def test_metrics_endpoint_exposes_decline_rate_specialty_dimension() -> None:
    response = TestClient(app).get("/metrics")

    decline_rate = {
        metric["id"]: metric
        for metric in response.json()["metrics"]
    }["decline_rate"]

    assert decline_rate["allowed_dimensions"] == [
        "consultant_specialty",
        "diagnosis_category",
        "month",
        "plan_tier",
        "region",
    ]
    assert "claim_lines.provider_id -> providers.id (many_to_one)" in decline_rate["join_preview"]


def test_metrics_endpoint_exposes_paid_claims_bridge_join() -> None:
    response = TestClient(app).get("/metrics")

    paid_claims = {
        metric["id"]: metric
        for metric in response.json()["metrics"]
    }["paid_claims"]

    assert paid_claims["allowed_dimensions"] == [
        "diagnosis_category",
        "month",
        "plan_tier",
        "region",
    ]
    assert "claim_lines.claim_id -> claims.id (many_to_one)" in paid_claims["join_preview"]
    assert "claims.member_id -> members.id (many_to_one)" in paid_claims["join_preview"]


def test_metrics_endpoint_exposes_expanded_governed_metrics() -> None:
    response = TestClient(app).get("/metrics")

    metrics = {metric["id"]: metric for metric in response.json()["metrics"]}

    assert metrics["out_of_network_rate"]["required_tables"] == [
        "claim_lines",
        "providers",
    ]
    assert (
        "claim_lines.provider_id -> providers.id (many_to_one)"
        in metrics["out_of_network_rate"]["join_preview"]
    )
    assert metrics["premium_per_member"]["currency"] == "GBP"
