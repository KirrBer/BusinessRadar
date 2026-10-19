import numpy as np
import pandas as pd
from shapely import contains_xy

from ml_core.config import RANDOM_STATE
from ml_core.districts import load_district_geometries, load_districts
from ml_core.features import FEATURE_COLS, TARGET_COL


def _sample_points(geometry, count: int, rng: np.random.Generator) -> np.ndarray:
    min_lon, min_lat, max_lon, max_lat = geometry.bounds
    batches = []
    sampled = 0

    while sampled < count:
        batch_size = max(64, (count - sampled) * 2)
        longitudes = rng.uniform(min_lon, max_lon, batch_size)
        latitudes = rng.uniform(min_lat, max_lat, batch_size)
        inside = contains_xy(geometry, longitudes, latitudes)
        accepted = np.column_stack((longitudes[inside], latitudes[inside]))
        if len(accepted):
            accepted = accepted[:count - sampled]
            batches.append(accepted)
            sampled += len(accepted)

    return np.concatenate(batches)


def make_locations(n: int = 6000, n_poles: int = 6) -> pd.DataFrame:
    """Generate synthetic locations inside Saint Petersburg districts."""
    if n < 0:
        raise ValueError("n must not be negative")
    if n_poles < 1:
        raise ValueError("n_poles must be positive")
    if n == 0:
        return pd.DataFrame(columns=[*FEATURE_COLS, TARGET_COL])

    rng = np.random.default_rng(RANDOM_STATE)
    districts = load_districts()
    geometries = load_district_geometries()
    weights = np.array([
        geometry.area * feature["properties"]["pop_density"]
        for geometry, feature in zip(geometries, districts, strict=True)
    ])
    district_counts = rng.multinomial(n, weights / weights.sum())
    frames = []

    for geometry, feature, count in zip(
        geometries,
        districts,
        district_counts,
        strict=True,
    ):
        if count == 0:
            continue

        profile = feature["properties"]
        coordinates = _sample_points(geometry, int(count), rng)
        poles = _sample_points(geometry, n_poles, rng)
        latitude_scale = np.cos(np.deg2rad(coordinates[:, 1]))
        distances = np.sqrt(
            ((coordinates[:, None, 0] - poles[None, :, 0]) * latitude_scale[:, None]) ** 2
            + (coordinates[:, None, 1] - poles[None, :, 1]) ** 2
        )
        activity = np.exp(-distances.min(axis=1) / 0.025)

        traffic = profile["traffic"] * (0.65 + 0.35 * activity) * rng.lognormal(0, 0.22, count)
        pop_density = profile["pop_density"] * (0.7 + 0.3 * activity) * rng.lognormal(0, 0.17, count)
        income_area = np.clip(rng.normal(profile["income_area"], 0.13, count), 0.3, 1.8)
        competitors = rng.poisson(profile["competitors"] + 0.35 * activity, count).astype(float)
        avg_check = rng.normal(850, 180, count).clip(250, 2500)
        peak_factor = rng.beta(2, 5, count)
        rent_cost = np.clip(rng.normal(profile["rent_cost"], 0.1, count), 0.05, 1)

        baseline = (
            0.45 * np.log1p(traffic)
            + 0.25 * np.log1p(pop_density)
            + 0.15 * income_area
            + 0.1 * peak_factor
            - 0.2 * np.log1p(competitors)
            + 0.05 * avg_check / 1000
        )
        demand = np.exp(baseline) * rng.normal(1, 0.18, count)
        frames.append(pd.DataFrame({
            "lat": coordinates[:, 1],
            "lon": coordinates[:, 0],
            "traffic": traffic,
            "pop_density": pop_density,
            "competitors": competitors,
            "avg_check": avg_check,
            "peak_factor": peak_factor,
            "income_area": income_area,
            "rent_cost": rent_cost,
            "demand": demand.clip(min=0),
        }))

    return pd.concat(frames, ignore_index=True).sample(
        frac=1,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)