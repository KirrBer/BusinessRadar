from __future__ import annotations
import logging, time, functools
from pathlib import Path
import pandas as pd

log = logging.getLogger("ml_core.adapters")

# ТОЧНО те же required-списки, что проверяет data_pipeline._read_csv.
# Если команда поменяла схему здесь — падай сразу, а не лови KeyError в обучении.
SCHEMA = {
    "addresses.csv":        ["location_id", "lat", "lon"],
    "area_metrics.csv":     ["location_id", "traffic", "pop_density"],
    "transactions.csv":     ["location_id", "amount", "transaction_at"],
    "competitors.csv":      ["location_id", "competitors"],
    "property_metrics.csv": ["location_id", "rent_per_sqm", "income_area"],
}

def data_dir() -> Path:
    import os
    p = Path(os.environ.get("BUSINESSRADAR_DATA_DIR", "data"))
    p.mkdir(parents=True, exist_ok=True)
    return p

def write_csv(df: pd.DataFrame, filename: str) -> Path:
    required = SCHEMA[filename]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"{filename}: адаптер вернул без колонок {missing}")
    df = df[required]                      # фиксируем порядок = контракт
    if df["location_id"].duplicated().any() and filename != "transactions.csv":
        raise ValueError(f"{filename}: location_id не уникален (кроме transactions)")
    path = data_dir() / filename
    df.to_csv(path, index=False)
    log.info("записан %s: %d строк", path.name, len(df))
    return path

def retry(times: int = 3, backoff: float = 1.5):
    """Сеть/лимиты API падают транзиентно — ретраим, а не крашим весь билд."""
    def deco(fn):
        @functools.wraps(fn)
        def wrap(*a, **k):
            for i in range(times):
                try:
                    return fn(*a, **k)
                except Exception as e:            # noqa: BLE001
                    if i == times - 1:
                        raise
                    log.warning("%s: попытка %d упала (%s), повтор через %.1fs",
                                fn.__name__, i + 1, e, backoff ** i)
                    time.sleep(backoff ** i)
        return wrap
    return deco