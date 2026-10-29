from ml_core.inference import predict_location
from ml_core.features import FEATURE_COLS
from ml_core.districts import load_district_geometries
from ml_core.synthetic_data import make_locations
from shapely import contains_xy
import numpy as np

GOOD = {"lat":59.934,"lon":30.335,"traffic":900,"pop_density":320,"competitors":1,
        "avg_check":700,"peak_factor":0.6,"income_area":1.4,"rent_cost":0.4}
BAD  = {**GOOD, "traffic":80,"pop_density":80,"competitors":9,"rent_cost":0.9}

def test_score_monotonic():
    assert predict_location(GOOD)["score"] > predict_location(BAD)["score"]

def test_score_range_and_keys():
    out = predict_location(GOOD)
    assert 1 <= out["score"] <= 10
    assert set(out) >= {"score","demand_forecast","demand_percentile",
                        "cluster_id","cluster_name","recommendation_text"}

def test_validate_rejects_garbage():
    try:
        predict_location({"lat":0}); assert False
    except ValueError:
        pass


def test_validate_rejects_non_finite_values():
    try:
        predict_location({**GOOD, "traffic": float("nan")})
        assert False
    except ValueError:
        pass


def test_synthetic_locations_are_inside_spb_districts():
    data = make_locations(n=240)
    inside = np.zeros(len(data), dtype=bool)

    for geometry in load_district_geometries():
        inside |= contains_xy(geometry, data["lon"].to_numpy(), data["lat"].to_numpy())

    assert inside.all()