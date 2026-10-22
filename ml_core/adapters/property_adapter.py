from __future__ import annotations
import pandas as pd
from ml_core.adapters._geo_context import all_location_ids, profile
from ml_core.adapters.base import write_csv, retry, log

@retry()
def _cian_rent(lat: float, lon: float, radius_m: int, key: str) -> float:
    # БОЕВОЙ: api.cian.ru/search-offers/v2/search-offers.json (партнёрский ключ),
    #   медианная ставка аренды за м2 по коммерческим лотам в радиусе.
    # Авито публичного API аренды НЕТ -> в проде только договор/официальный фид, не парсинг.
    raise NotImplementedError("нет ЦИАН-ключа — fallback на стенд")

def fetch() -> pd.DataFrame:
    key = __import__("os").environ.get("CIAN_KEY", "")
    rows = []
    for i in all_location_ids():
        p = profile(i)
        try:
            rent = _cian_rent(p["lat"], p["lon"], 300, key) if key else p["rent_per_sqm"]
        except Exception as e:                       # noqa: BLE001
            log.warning("ЦИАН недоступен (%s), беру стенд-аренду", e); rent = p["rent_per_sqm"]
        # income_area — из данных банка о доходах клиентов района (BOEVOY: SQL к dm.ref_area_income)
        rows.append({"location_id": i, "rent_per_sqm": rent, "income_area": p["income_area"]})
    return pd.DataFrame(rows)

if __name__ == "__main__":
    write_csv(fetch(), "property_metrics.csv")