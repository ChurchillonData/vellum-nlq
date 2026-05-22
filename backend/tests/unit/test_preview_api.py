from fastapi.testclient import TestClient

from app.main import app


def test_preview_endpoint_returns_loss_ratio_sql_and_provenance() -> None:
    response = TestClient(app).post(
        "/queries/preview",
        json={
            "metric_id": "loss_ratio",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "plan_tier": "Comprehensive",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["metric_id"] == "loss_ratio"
    assert "%(start_date)s" in body["sql"]
    assert "Comprehensive" not in body["sql"]
    assert body["parameters"]["plan_tier"] == "Comprehensive"
    assert body["provenance"]["time_anchor"] == "claims.incurred_date"
    assert body["provenance"]["result_shape"] == {
        "columns": ["loss_ratio"],
        "grain": "single_metric",
    }
    assert body["validation"]["passed"] is True
    assert "select_only" in body["validation"]["rules_checked"]


def test_preview_endpoint_reports_unknown_metric() -> None:
    response = TestClient(app).post(
        "/queries/preview",
        json={
            "metric_id": "not_a_metric",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "unknown metric: not_a_metric"}


def test_preview_endpoint_rejects_reverse_date_range() -> None:
    response = TestClient(app).post(
        "/queries/preview",
        json={
            "metric_id": "loss_ratio",
            "start_date": "2026-03-31",
            "end_date": "2026-01-01",
        },
    )

    assert response.status_code == 422
