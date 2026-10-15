from functools import lru_cache
import joblib, json
import numpy as np, pandas as pd
from ml_core.config import ARTIFACTS
from ml_core.features import FEATURE_COLS, GEO_COLS, validate_features
from ml_core.recommender import generate_recommendation

@lru_cache(maxsize=1)            # грузим модели ОДИН раз, иначе каждый запрос читает диск
def _bundle():
    return (joblib.load(ARTIFACTS/"rf_demand.joblib"),
            joblib.load(ARTIFACTS/"kmeans.joblib"),
            json.loads((ARTIFACTS/"feature_stats.json").read_text()),
            json.loads((ARTIFACTS/"clusters.json").read_text()))

def predict_location(features: dict) -> dict:
    validate_features(features)
    rf, kmb, meta, cl = _bundle()
    row = pd.DataFrame([features])[FEATURE_COLS]          # порядок = как при обучении
    dp  = float(rf.predict(row)[0])
    q   = np.array(meta["demand_quantiles"])
    pct = float(np.searchsorted(q, dp)/len(q))
    score = int(np.clip(round(pct*9+1), 1, 10))           # скоринг = перцентиль спроса
    geo = np.array([[features[c] for c in GEO_COLS]])     # порядок = GEO_COLS
    cid = int(kmb["km"].predict(kmb["scaler"].transform(geo))[0])
    return {"score": score, "demand_forecast": round(dp,2), "demand_percentile": round(pct,3),
            "cluster_id": cid, "cluster_name": cl["cluster_names"][cid],
            "recommendation_text": generate_recommendation(score, pct,
                int(features["competitors"]), float(features["rent_cost"]),
                cl["cluster_names"][cid])}