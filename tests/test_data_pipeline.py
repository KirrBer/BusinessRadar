import pandas as pd

from ml_core.data_pipeline import load_locations


def test_load_locations_aggregates_real_source_exports(tmp_path):
    pd.DataFrame(
        [
            {"location_id": "a", "lat": 55.75, "lon": 37.62},
            {"location_id": "b", "lat": 55.76, "lon": 37.63},
        ]
    ).to_csv(tmp_path / "addresses.csv", index=False)
    pd.DataFrame(
        [
            {"location_id": "a", "traffic": 1000, "pop_density": 8000,
             "competitors": 2, "income_area": 1.2, "rent_cost": 0.4},
            {"location_id": "b", "traffic": 500, "pop_density": 4000,
             "competitors": 1, "income_area": 0.9, "rent_cost": 0.7},
        ]
    ).to_csv(tmp_path / "area_metrics.csv", index=False)
    pd.DataFrame(
        [
            {"location_id": "a", "amount": 700, "transaction_at": "2026-01-01 12:00"},
            {"location_id": "a", "amount": 900, "transaction_at": "2026-01-02 20:00"},
            {"location_id": "b", "amount": 400, "transaction_at": "2026-01-01 09:00"},
            {"location_id": "b", "amount": 600, "transaction_at": "2026-01-02 13:00"},
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
