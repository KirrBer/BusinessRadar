import math
from numbers import Real


# Признаки для Random Forest
FEATURE_COLS = ["lat", "lon", "traffic", "pop_density", "competitors",
                "avg_check", "peak_factor", "income_area", "rent_cost"]
# Колонки для K-Means 
GEO_COLS     = ["lat", "lon", "pop_density", "income_area", "traffic"]
TARGET_COL   = "demand"

def validate_features(features: dict) -> None:
    """Падает с понятной ошибкой, если пришли не те ключи/значения."""
    missing = [c for c in FEATURE_COLS if c not in features]
    if missing:
        raise ValueError(f"ML-ядро: не хватает признаков {missing}")

    for c in FEATURE_COLS:
        value = features[c]
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"ML-ядро: '{c}' должен быть числом")
        if not math.isfinite(value):
            raise ValueError(f"ML-ядро: '{c}' должен быть конечным числом")

    if not -90 <= features["lat"] <= 90:
        raise ValueError(f"ML-ядро: 'lat' вне диапазона [-90, 90] ({features['lat']})")
    if not -180 <= features["lon"] <= 180:
        raise ValueError(f"ML-ядро: 'lon' вне диапазона [-180, 180] ({features['lon']})")

    for c in ("traffic", "pop_density", "competitors", "avg_check", "rent_cost"):
        if features[c] < 0:
            raise ValueError(f"ML-ядро: '{c}' не может быть отрицательным ({features[c]})")
    if not 0 <= features["peak_factor"] <= 1:
        raise ValueError(
            f"ML-ядро: 'peak_factor' должен быть в диапазоне [0, 1] "
            f"({features['peak_factor']})"
        )
    if features["rent_cost"] > 1:
        raise ValueError(
            f"ML-ядро: 'rent_cost' должен быть в диапазоне [0, 1] "
            f"({features['rent_cost']})"
        )