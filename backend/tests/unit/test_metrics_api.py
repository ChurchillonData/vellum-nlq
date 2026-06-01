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
        "claim_frequency",
        "claim_severity",
        "decline_rate",
        "incurred_claims",
        "loss_ratio",
        "paid_claims",
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
    assert loss_ratio["allowed_dimensions"] == ["plan_tier", "region"]
    assert "claims.member_id -> members.id (many_to_one)" in loss_ratio["join_preview"]
    assert "premium.member_id -> members.id (many_to_one)" in loss_ratio["join_preview"]


def test_metrics_endpoint_exposes_decline_rate_specialty_dimension() -> None:
    response = TestClient(app).get("/metrics")

    decline_rate = {
        metric["id"]: metric
        for metric in response.json()["metrics"]
    }["decline_rate"]

    assert decline_rate["allowed_dimensions"] == [
        "plan_tier",
        "region",
        "consultant_specialty",
    ]
    assert "claim_lines.provider_id -> providers.id (many_to_one)" in decline_rate["join_preview"]


def test_metrics_endpoint_exposes_paid_claims_bridge_join() -> None:
    response = TestClient(app).get("/metrics")

    paid_claims = {
        metric["id"]: metric
        for metric in response.json()["metrics"]
    }["paid_claims"]

    assert "claim_lines.claim_id -> claims.id (many_to_one)" in paid_claims["join_preview"]
    assert "claims.member_id -> members.id (many_to_one)" in paid_claims["join_preview"]
