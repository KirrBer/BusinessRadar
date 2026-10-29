import json, joblib
import argparse
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from ml_core.config import RANDOM_STATE, ARTIFACTS
from ml_core.features import GEO_COLS
from ml_core.data_pipeline import load_locations
from ml_core.synthetic_data import make_locations

def name_clusters(centers):  # centers: [lat,lon,pop,income,traffic]
    med = np.median(centers, axis=0)
    out = []
    for _, _, pop, inc, tr in centers:
        out.append(f"{'плотный' if pop>med[2] else 'спальный'}·"
                   f"{'платёж.' if inc>med[3] else 'эконом'}·"
                   f"{'трафик.' if tr>med[4] else 'локальный'}")
    return out

def train(data_dir=None, demo=False):
    df = make_locations() if demo else load_locations(data_dir)
    Xg = df[GEO_COLS].values
    scaler = StandardScaler().fit(Xg)            # без скейла градусы зададут признаки
    Xs = scaler.transform(Xg)
    silhouette_sample_size = min(2000, len(Xs))
    scores = {}
    for k in range(4, 13):
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(Xs)
        scores[k] = silhouette_score(
            Xs,
            km.labels_,
            sample_size=silhouette_sample_size,
            random_state=RANDOM_STATE,
        )
    best_k = max(scores, key=scores.get)
    km = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10).fit(Xs)
    centers_geo = scaler.inverse_transform(km.cluster_centers_)
    joblib.dump({"scaler": scaler, "km": km}, ARTIFACTS / "kmeans.joblib")
    (ARTIFACTS / "clusters.json").write_text(json.dumps({
        "best_k": best_k, "silhouette": round(float(scores[best_k]), 3),
        "centers_geo": centers_geo.tolist(),
        "cluster_names": name_clusters(centers_geo)}, ensure_ascii=False))
    print("K-Means: k =", best_k, "silhouette =", round(scores[best_k], 3))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    train(args.data_dir, args.demo)