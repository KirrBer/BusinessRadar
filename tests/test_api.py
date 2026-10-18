from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)
FEATURES = {
    "lat": 55.75,
    "lon": 37.62,
    "traffic": 900,
    "pop_density": 8000,
    "competitors": 1,
    "avg_check": 700,
    "peak_factor": 0.6,
    "income_area": 1.4,
    "rent_cost": 0.4,
}


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_is_not_served_by_api():
    response = client.get("/")

    assert response.status_code == 404


def test_predict_returns_prediction(monkeypatch):
    expected = {
        "score": 8,
        "demand_forecast": 12.3,
        "demand_percentile": 0.8,
        "cluster_id": 2,
        "cluster_name": "dense",
        "recommendation_text": "Good location",
    }
    monkeypatch.setattr(main, "predict_location", lambda features: expected)

    response = client.post("/api/v1/predict", json=FEATURES)

    assert response.status_code == 200
    assert response.json() == expected


def test_predict_rejects_negative_features():
    response = client.post(
        "/api/v1/predict", json={**FEATURES, "traffic": -1}
    )

    assert response.status_code == 422


def test_predict_rejects_out_of_range_features():
    response = client.post(
        "/api/v1/predict", json={**FEATURES, "peak_factor": 1.1}
    )

    assert response.status_code == 422