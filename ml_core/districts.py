import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
from shapely import force_2d
from shapely import contains_xy
from shapely.geometry import shape

from ml_core.data_pipeline import load_locations


DATA_FILE = Path(__file__).resolve().parent / "data" / "spb_districts.geojson"

# These are illustrative inputs for synthetic training data, not official statistics.
DISTRICT_PROFILES = (
    {"id": "adm", "name": "Адмиралтейский район", "traffic": 760, "pop_density": 330, "competitors": 5, "income_area": 1.08, "rent_cost": 0.88},
    {"id": "vas", "name": "Василеостровский район", "traffic": 570, "pop_density": 270, "competitors": 4, "income_area": 1.02, "rent_cost": 0.75},
    {"id": "vyb", "name": "Выборгский район", "traffic": 450, "pop_density": 215, "competitors": 3, "income_area": 1.08, "rent_cost": 0.68},
    {"id": "kal", "name": "Калининский район", "traffic": 490, "pop_density": 245, "competitors": 4, "income_area": 1.0, "rent_cost": 0.64},
    {"id": "kir", "name": "Кировский район", "traffic": 365, "pop_density": 190, "competitors": 3, "income_area": 0.92, "rent_cost": 0.53},
    {"id": "kol", "name": "Колпинский район", "traffic": 265, "pop_density": 135, "competitors": 2, "income_area": 0.82, "rent_cost": 0.43},
    {"id": "kgr", "name": "Красногвардейский район", "traffic": 350, "pop_density": 190, "competitors": 3, "income_area": 0.94, "rent_cost": 0.55},
    {"id": "krs", "name": "Красносельский район", "traffic": 245, "pop_density": 145, "competitors": 2, "income_area": 0.91, "rent_cost": 0.44},
    {"id": "kro", "name": "Кронштадтский район", "traffic": 190, "pop_density": 120, "competitors": 1, "income_area": 0.94, "rent_cost": 0.42},
    {"id": "kur", "name": "Курортный район", "traffic": 300, "pop_density": 70, "competitors": 1, "income_area": 1.28, "rent_cost": 0.78},
    {"id": "mos", "name": "Московский район", "traffic": 690, "pop_density": 205, "competitors": 4, "income_area": 1.16, "rent_cost": 0.76},
    {"id": "nev", "name": "Невский район", "traffic": 540, "pop_density": 235, "competitors": 4, "income_area": 0.96, "rent_cost": 0.6},
    {"id": "pet", "name": "Петроградский район", "traffic": 720, "pop_density": 310, "competitors": 4, "income_area": 1.3, "rent_cost": 0.94},
    {"id": "pvd", "name": "Петродворцовый район", "traffic": 235, "pop_density": 95, "competitors": 1, "income_area": 1.13, "rent_cost": 0.58},
    {"id": "pri", "name": "Приморский район", "traffic": 620, "pop_density": 205, "competitors": 3, "income_area": 1.2, "rent_cost": 0.78},
    {"id": "pus", "name": "Пушкинский район", "traffic": 310, "pop_density": 125, "competitors": 2, "income_area": 1.02, "rent_cost": 0.54},
    {"id": "fru", "name": "Фрунзенский район", "traffic": 510, "pop_density": 250, "competitors": 4, "income_area": 0.98, "rent_cost": 0.59},
    {"id": "cen", "name": "Центральный район", "traffic": 900, "pop_density": 350, "competitors": 6, "income_area": 1.32, "rent_cost": 1.0},
)


@lru_cache(maxsize=1)
def load_districts() -> tuple[dict, ...]:
    collection = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    profiles = {profile["name"]: profile for profile in DISTRICT_PROFILES}
    features = []

    for source_feature in collection["features"]:
        name = source_feature["properties"]["name"]
        profile = profiles[name]
        geometry = force_2d(shape(source_feature["geometry"]))
        center = geometry.representative_point()
        features.append({
            "type": "Feature",
            "properties": {
                **profile,
                "osm_id": source_feature["properties"]["osm_id"],
                "center": {"lat": center.y, "lon": center.x},
            },
            "geometry": source_feature["geometry"],
        })

    if len(features) != len(DISTRICT_PROFILES):
        raise ValueError("GeoJSON must contain all 18 Saint Petersburg districts")
    return tuple(features)


@lru_cache(maxsize=1)
def load_district_geometries() -> tuple:
    return tuple(shape(feature["geometry"]) for feature in load_districts())


def district_feature_collection(locations: pd.DataFrame | None = None) -> dict:
    observations = load_locations() if locations is None else locations
    longitudes = observations["lon"].to_numpy()
    latitudes = observations["lat"].to_numpy()
    metrics = (
        "traffic",
        "pop_density",
        "competitors",
        "avg_check",
        "peak_factor",
        "income_area",
        "rent_cost",
    )
    features = []

    for source_feature, geometry in zip(load_districts(), load_district_geometries(), strict=True):
        properties = source_feature["properties"]
        inside = contains_xy(geometry, longitudes, latitudes)
        district_rows = observations.loc[inside]
        summary = {
            metric: float(district_rows[metric].median()) if not district_rows.empty else None
            for metric in metrics
        }
        features.append({
            "type": "Feature",
            "properties": {
                "id": properties["id"],
                "name": properties["name"],
                "osm_id": properties["osm_id"],
                "center": properties["center"],
                "sample_count": len(district_rows),
                **summary,
            },
            "geometry": source_feature["geometry"],
        })

    return {
        "type": "FeatureCollection",
        "name": "Районы Санкт-Петербурга",
        "attribution": "© OpenStreetMap contributors",
        "license": "ODbL-1.0",
        "source": "https://www.openstreetmap.org/",
        "features": features,
    }