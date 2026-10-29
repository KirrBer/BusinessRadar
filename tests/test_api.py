import pandas as pd
from fastapi.testclient import TestClient

from app import main
from ml_core.districts import load_districts


client = TestClient(main.app)
FEATURES = {
    "lat": 59.934,
    "lon": 30.335,
    "traffic": 900,
    "pop_density": 300,
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


def test_district_geojson_contains_all_spb_districts(monkeypatch):
    central = next(
        feature["properties"]
        for feature in load_districts()
        if feature["properties"]["id"] == "cen"
    )
    monkeypatch.setattr(main, "load_locations", lambda: pd.DataFrame([{
        "lat": central["center"]["lat"],
        "lon": central["center"]["lon"],
        "traffic": 240,
        "pop_density": 120,
        "competitors": 2,
        "avg_check": 700,
        "peak_factor": 0.3,
        "income_area": 1.0,
        "rent_cost": 0.5,
        "demand": 12,
    }]))

    response = client.get("/api/v1/districts")

    assert response.status_code == 200
    data = response.json()
    assert data["license"] == "ODbL-1.0"
    assert len(data["features"]) == 18
    assert all(feature["geometry"]["type"] in {"Polygon", "MultiPolygon"} for feature in data["features"])
    assert {feature["properties"]["name"] for feature in data["features"]} >= {"Центральный район", "Петроградский район"}
    central_data = next(feature["properties"] for feature in data["features"] if feature["properties"]["id"] == "cen")
    assert central_data["sample_count"] == 1
    assert central_data["traffic"] == 240


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