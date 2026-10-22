from __future__ import annotations
import pandas as pd
from ml_core.adapters._geo_context import all_location_ids, profile
from ml_core.adapters.base import write_csv, retry, log

@retry()
def _two_gis_traffic(lat: float, lon: float, token: str) -> float:
    # БОЕВОЙ: catalog.api.2gis.com/3.0 — coverage/traffic по точке, header access_token=token
    # import requests
    # r = requests.get("https://catalog.api.2gis.com/3.0/items/geocode",
    #                  params={"lat": lat, "lon": lon, "fields": "coverage",
    #                          "access_token": token}, timeout=10)
    # r.raise_for_status(); return float(r.json()["result"]["traffic_index"])
    raise NotImplementedError("нет 2GIS-токена — fallback на стенд")

def fetch() -> pd.DataFrame:
    token = __import__("os").environ.get("TWOGIS_TOKEN", "")
    rows = []
    for i in all_location_ids():
        p = profile(i)
        try:
            traffic = _two_gis_traffic(p["lat"], p["lon"], token) if token else p["traffic"]
        except Exception as e:                       # noqa: BLE001
            log.warning("2GIS недоступен (%s), беру стенд-трафик", e); traffic = p["traffic"]
        # Росстат: pop_density по коду муниципалитета из открытой выгрузки (fedstat/rosstat CSV)
        rows.append({"location_id": i, "traffic": traffic, "pop_density": p["pop_density"]})
    return pd.DataFrame(rows)

if __name__ == "__main__":
    write_csv(fetch(), "area_metrics.csv")