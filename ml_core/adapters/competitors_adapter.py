from __future__ import annotations
import pandas as pd
from ml_core.adapters._geo_context import all_location_ids, profile
from ml_core.adapters.base import write_csv, retry, log

@retry()
def _yandex_competitors(lat: float, lon: float, radius_m: int, apikey: str, mcc: str) -> int:
    # БОЕВОЙ: search-maps.yandex.ru/v1/?text=<категория>&ll=lon,lat&spn=...&apikey=apikey
    #   count найденных организаций той же категории в радиусе = competitors.
    # ВНИМАНИЕ: массовый парсинг карт = серая зона ToS; в проде — официальный Геокодер/Поиск
    #   по коммерческому тарифу или договор с Яндекс.Бизнес. Не долби бесплатный лимит.
    # import requests
    # r = requests.get("https://search-maps.yandex.ru/v1/", params={...}, timeout=10)
    # return len(r.json().get("features", []))
    raise NotImplementedError("нет Яндекс-ключа — fallback на стенд")

def fetch() -> pd.DataFrame:
    key = __import__("os").environ.get("YANDEX_MAPS_KEY", "")
    rows = []
    for i in all_location_ids():
        p = profile(i)
        try:
            c = _yandex_competitors(p["lat"], p["lon"], 500, key, "cafe") if key else int(p["competitors"])
        except Exception as e:                       # noqa: BLE001
            log.warning("Яндекс недоступен (%s), беру стенд-конкурентов", e); c = int(p["competitors"])
        rows.append({"location_id": i, "competitors": c})
    return pd.DataFrame(rows)

if __name__ == "__main__":
    write_csv(fetch(), "competitors.csv")