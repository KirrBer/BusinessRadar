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
    for c in ("traffic", "pop_density", "competitors", "rent_cost"):
        if features[c] < 0:
            raise ValueError(f"ML-ядро: '{c}' не может быть отрицательным ({features[c]})")