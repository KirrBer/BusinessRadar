import pandas as pd

from ml_core.data_pipeline import load_locations
from ml_core.districts import load_districts


def test_load_locations_aggregates_real_source_exports(tmp_path):
    central = next(
        feature["properties"]
        for feature in load_districts()
        if feature["properties"]["id"] == "cen"
    )
    lat = central["center"]["lat"]
    lon = central["center"]["lon"]
    pd.DataFrame(
        [
            {"location_id": "a", "lat": lat, "lon": lon},
            {"location_id": "b", "lat": lat, "lon": lon},
            {"location_id": "outside", "lat": 55.75, "lon": 37.62},
        ]
    ).to_csv(tmp_path / "addresses.csv", index=False)
    pd.DataFrame(
        [
            {"location_id": "a", "traffic": 1000, "pop_density": 8000,
             "competitors": 2, "income_area": 1.2, "rent_cost": 0.4},
            {"location_id": "b", "traffic": 500, "pop_density": 4000,
             "competitors": 1, "income_area": 0.9, "rent_cost": 0.7},
            {"location_id": "outside", "traffic": 700, "pop_density": 5000,
             "competitors": 2, "income_area": 1.0, "rent_cost": 0.5},
        ]
    ).to_csv(tmp_path / "area_metrics.csv", index=False)
    pd.DataFrame(
        [
            {"location_id": "a", "amount": 700, "transaction_at": "2026-01-01 12:00"},
            {"location_id": "a", "amount": 900, "transaction_at": "2026-01-02 20:00"},
            {"location_id": "b", "amount": 400, "transaction_at": "2026-01-01 09:00"},
            {"location_id": "b", "amount": 600, "transaction_at": "2026-01-02 13:00"},
            {"location_id": "outside", "amount": 800, "transaction_at": "2026-01-01 13:00"},
            {"location_id": "outside", "amount": 900, "transaction_at": "2026-01-02 14:00"},
        ]
    ).to_csv(tmp_path / "transactions.csv", index=False)

    result = load_locations(tmp_path)

    assert list(result.columns) == [
        "lat", "lon", "traffic", "pop_density", "competitors", "avg_check",
        "peak_factor", "income_area", "rent_cost", "demand",
    ]
    assert result.loc[0, "avg_check"] == 800
    assert result.loc[0, "demand"] == 1
    assert result.loc[0, "peak_factor"] == 0.5
    assert len(result) == 2
    assert result["lat"].between(59, 61).all()


def test_load_locations_never_falls_back_when_real_data_is_missing(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError, match="addresses.csv"):
        load_locations(tmp_path)
