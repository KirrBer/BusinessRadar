import json, joblib
import argparse
import numpy as np, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from ml_core.config import RANDOM_STATE, ARTIFACTS
from ml_core.features import FEATURE_COLS, TARGET_COL
from ml_core.data_pipeline import load_locations
from ml_core.synthetic_data import make_locations

def build_rf():
    return Pipeline([("scale", StandardScaler()),
        ("rf", RandomForestRegressor(n_estimators=400, min_samples_leaf=3,
                                     random_state=RANDOM_STATE, n_jobs=-1))])

def train(data_dir=None, demo=False):
    df = make_locations() if demo else load_locations(data_dir)
    X, y = df[FEATURE_COLS], df[TARGET_COL]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
    pipe = build_rf().fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    report = {"mae": round(float(mean_absolute_error(yte, pred)), 3),
              "r2":  round(float(r2_score(yte, pred)), 3),
               "source": "synthetic" if demo else "pipeline",
              "feature_importance": dict(zip(FEATURE_COLS,
                  np.round(pipe.named_steps["rf"].feature_importances_, 4)))}
    joblib.dump(pipe, ARTIFACTS / "rf_demand.joblib")
    q = np.quantile(ytr, np.linspace(0, 1, 101)).tolist()
    (ARTIFACTS / "feature_stats.json").write_text(
        json.dumps({"demand_quantiles": q, "report": report}, ensure_ascii=False))
    print("RF:", report["mae"], report["r2"])
    print("top-3 признака:", sorted(report["feature_importance"].items(),
                                    key=lambda kv: -kv[1])[:3])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    train(args.data_dir, args.demo)