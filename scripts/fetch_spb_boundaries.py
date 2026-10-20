import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from shapely import force_2d
from shapely.geometry import mapping, shape

from ml_core.districts import DISTRICT_PROFILES, DATA_FILE


def fetch_boundary(name: str) -> dict:
    query = urlencode({
        "q": f"{name}, Санкт-Петербург, Россия",
        "format": "jsonv2",
        "polygon_geojson": 1,
        "extratags": 1,
        "limit": 5,
    })
    request = Request(
        f"https://nominatim.openstreetmap.org/search?{query}",
        headers={"User-Agent": "BusinessRadar/0.1 (administrative district boundary import)"},
    )
    with urlopen(request, timeout=30) as response:
        candidates = json.load(response)

    for candidate in candidates:
        if (
            candidate.get("category") == "boundary"
            and candidate.get("type") == "administrative"
            and candidate.get("osm_type") == "relation"
            and candidate.get("extratags", {}).get("admin_level") == "5"
            and candidate.get("geojson")
        ):
            geometry = force_2d(shape(candidate["geojson"])).simplify(
                0.00015,
                preserve_topology=True,
            )
            return {
                "type": "Feature",
                "properties": {"name": name, "osm_id": candidate["osm_id"]},
                "geometry": mapping(geometry),
            }

    raise ValueError(f"No admin_level=5 OSM boundary found for {name}")


def main() -> None:
    features = []
    for index, profile in enumerate(DISTRICT_PROFILES):
        if index:
            time.sleep(1.1)
        features.append(fetch_boundary(profile["name"]))
        print(f"Fetched {profile['name']} ({index + 1}/{len(DISTRICT_PROFILES)})")

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    collection = {
        "type": "FeatureCollection",
        "name": "Районы Санкт-Петербурга",
        "attribution": "© OpenStreetMap contributors",
        "license": "ODbL-1.0",
        "source": "https://www.openstreetmap.org/",
        "retrieved_at": datetime.now(UTC).date().isoformat(),
        "features": features,
    }
    DATA_FILE.write_text(
        json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Saved {len(features)} district boundaries to {DATA_FILE}")


if __name__ == "__main__":
    main()