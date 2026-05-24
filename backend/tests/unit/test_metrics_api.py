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
    assert loss_ratio["version"] == "2.5.0"
