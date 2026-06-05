from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_active_catalogue() -> None:
    response = TestClient(app).get("/health")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["catalogue"] == "health-uk"
    assert body["data_window"]["month_count"] == 18
    assert body["data_window"]["start_date"] <= body["data_window"]["end_date"]


def test_cors_allows_configured_frontend_origin() -> None:
    response = TestClient(app).options(
        "/health",
        headers={
            "Access-Control-Request-Method": "GET",
            "Origin": "http://127.0.0.1:5173",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
