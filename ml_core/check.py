import json
import numpy as np
from ml_core.config import ARTIFACTS
from ml_core.inference import predict_location

# Метка читается по ТОМУ ЖЕ пути, куда пишет train (ARTIFACTS из config).
# Путь печатаем ниже — если config.py разъехался мерджем, это будет видно, а не предположено.
_stats_path = ARTIFACTS / "feature_stats.json"
meta = json.loads(_stats_path.read_text())
src = meta.get("report", {}).get("source", meta.get("source", "synthetic"))         # ЕДИНСТВЕННОЕ присваивание src

# ЕДИНСТВЕННОЕ присваивание df — строго в ветках. Никаких df= вне if/else,
# никаких повторных src= ниже по файлу (именно такой хвост и ломал печать).
if src == "pipeline":
    from ml_core.data_pipeline import load_locations
    df = load_locations()                       # упадёт ГРОМКО, если data/ нет — это правильно
else:
    from ml_core.synthetic_data import make_locations
    df = make_locations()

q = df["demand"].quantile
cols = [c for c in df.columns if c != "demand"]

def loc_from_row(row):
    return {c: float(row[c]) for c in cols}

gold   = loc_from_row(df.loc[df["demand"].idxmax()])
desert = loc_from_row(df.loc[df["demand"].idxmin()])
hot_rows = df[(df["demand"] >= q(0.9)) & (df["competitors"] >= 5)]
hot = loc_from_row(hot_rows.iloc[0]) if len(hot_rows) else gold
trap_rows = df[df["rent_cost"] >= 0.85]
if trap_rows.empty:
    trap_rows = df.nlargest(1, "rent_cost")      # симметрично hot: гарантированно непусто
trap = loc_from_row(trap_rows.iloc[0])
outlier = {**gold, "traffic": gold["traffic"] * 10, "pop_density": gold["pop_density"] * 10}

cases = {"золотая": gold, "перегретая": hot, "пустыня": desert,
         "ловушка_аренды": trap, "выброс": outlier}
expect = {"золотая": lambda r: r["score"] >= 8,
          "пустыня": lambda r: r["score"] <= 3,
          "перегретая": lambda r: "уникаль" in r["recommendation_text"].lower() or "отстро" in r["recommendation_text"].lower(),
          "ловушка_аренды": lambda r: "аренда" in r["recommendation_text"].lower(),
          "выброс": lambda r: np.isfinite(r["score"]) and 1 <= r["score"] <= 10}

# Печатаем ПУТЬ и ЗНАЧЕНИЕ метки — разъезд ARTIFACTS виден строкой выше, а не угадывается.
print(f"check: метка source={src!r} из {_stats_path} (существует={_stats_path.exists()})")
print(f"check: источник эталонов = {src} (строк в df = {len(df)})")
clusters = set()
for name, f in cases.items():
    r = predict_location(f)
    clusters.add(r["cluster_id"])
    ok = expect[name](r)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: score={r['score']} pct={r['demand_percentile']} cluster={r['cluster_name']}")
    print("   ", r["recommendation_text"], "\n")
print("разных кластеров в тесте:", len(clusters), "(должно быть > 1)")