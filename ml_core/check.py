import numpy as np
from ml_core.synthetic_data import make_locations
from ml_core.inference import predict_location

df = make_locations()
q = df["demand"].quantile
cols = [c for c in df.columns if c != "demand"]

def loc_from_row(row):
    return {c: float(row[c]) for c in cols}

# эталоны берём ИЗ данных, а не выдумываем
gold   = loc_from_row(df.loc[df["demand"].idxmax()])                 # дно->потолок спроса
desert = loc_from_row(df.loc[df["demand"].idxmin()])                 # абсолютное дно
hot    = df[(df["demand"] >= q(0.9)) & (df["competitors"] >= 5)]     # высокий спрос + толпа
trap   = df[df["rent_cost"] >= 0.85].iloc[0]                         # дорогая аренда
trap   = loc_from_row(trap)
hot    = loc_from_row(hot.iloc[0]) if len(hot) else gold
# рукотворный выброс на валидных координатах (проверка на NaN/inf)
outlier = {**gold, "traffic": gold["traffic"] * 10, "pop_density": gold["pop_density"] * 10}

cases = {"золотая": gold, "перегретая": hot, "пустыня": desert,
         "ловушка_аренды": trap, "выброс": outlier}
expect = {"золотая": lambda r: r["score"] >= 8,
          "пустыня": lambda r: r["score"] <= 3,
          "перегретая": lambda r: "уникаль" in r["recommendation_text"].lower() or "отстро" in r["recommendation_text"].lower(),
          "ловушка_аренды": lambda r: "аренда" in r["recommendation_text"].lower(),
          "выброс": lambda r: np.isfinite(r["score"]) and 1 <= r["score"] <= 10}

clusters = set()
for name, f in cases.items():
    r = predict_location(f)
    clusters.add(r["cluster_id"])
    ok = expect[name](r)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: score={r['score']} pct={r['demand_percentile']} cluster={r['cluster_name']}")
    print("   ", r["recommendation_text"], "\n")

print("разных кластеров в тесте:", len(clusters), "(должно быть > 1)")