from ml_core.inference import predict_location
from ml_core.features import FEATURE_COLS

GOOD = {"lat":55.75,"lon":37.62,"traffic":900,"pop_density":8000,"competitors":1,
        "avg_check":700,"peak_factor":0.6,"income_area":1.4,"rent_cost":0.4}
BAD  = {**GOOD, "traffic":80,"pop_density":500,"competitors":9,"rent_cost":0.9}

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