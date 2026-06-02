from fastapi.testclient import TestClient

from app.main import app


def test_mapping_coverage_endpoint_returns_example_mapping() -> None:
    response = TestClient(app).get("/mappings/example-insurer/coverage")

    body = response.json()

    assert response.status_code == 200
    assert body["partner"] == "example-insurer"
    assert body["catalogue"] == "health-uk"
    assert body["mapped_tables"] == body["total_tables"] == 10
    assert body["mapped_columns"] == body["total_columns"] == 53
    assert body["missing_tables"] == []
    assert body["missing_columns"] == []


def test_mapping_coverage_endpoint_returns_404_for_unknown_partner() -> None:
    response = TestClient(app).get("/mappings/unknown-insurer/coverage")

    assert response.status_code == 404
    assert response.json()["detail"] == "mapping not found: unknown-insurer"
