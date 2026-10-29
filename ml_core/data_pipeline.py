from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


def _read_csv(data_dir: Path, filename: str, required: list[str]) -> pd.DataFrame:
    path = data_dir / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Не найден файл {path}. Подготовьте выгрузку по схеме README.md."
        )
    frame = pd.read_csv(path)
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"{filename}: не хватает колонок {missing}")
    return frame


def load_locations(data_dir: str | Path | None = None) -> pd.DataFrame:
    """Собирает признаки из адресов, геоданных, недвижимости и транзакций.

    Источники намеренно представлены CSV-выгрузками: адаптеры 2GIS, Росстата,
    Яндекс.Карт, ЦИАН/Авито и эквайринга могут выгружать в эту стабильную схему
    без изменения ML-кода.
    """
    root = Path(data_dir or os.environ.get("BUSINESSRADAR_DATA_DIR", "data"))
    addresses = _read_csv(root, "addresses.csv", ["location_id", "lat", "lon"])
    metrics = _read_csv(
        root,
        "area_metrics.csv",
        ["location_id", "traffic", "pop_density"],
    )
    transactions = _read_csv(
        root,
        "transactions.csv",
        ["location_id", "amount", "transaction_at"],
    )

    if addresses["location_id"].duplicated().any():
        raise ValueError("addresses.csv: location_id должен быть уникальным")
    if metrics["location_id"].duplicated().any():
        raise ValueError("area_metrics.csv: допускается одна строка на location_id")
    if transactions.empty:
        raise ValueError("transactions.csv: выгрузка не должна быть пустой")

    transactions = transactions.copy()
    transactions["amount"] = pd.to_numeric(transactions["amount"], errors="coerce")
    if transactions["amount"].isna().any():
        raise ValueError("transactions.csv: amount содержит нечисловые значения")
    transactions["transaction_at"] = pd.to_datetime(
        transactions["transaction_at"], errors="coerce"
    )
    if transactions["transaction_at"].isna().any():
        raise ValueError("transactions.csv: transaction_at содержит неверные даты")
    if (transactions["amount"] < 0).any():
        raise ValueError("transactions.csv: amount не может быть отрицательным")

    observation_days = (
        transactions["transaction_at"].dt.normalize().max()
        - transactions["transaction_at"].dt.normalize().min()
    ).days + 1
    tx = transactions.groupby("location_id").agg(
        avg_check=("amount", "mean"),
        transaction_count=("amount", "size"),
        peak_transactions=(
            "transaction_at",
            lambda values: ((values.dt.hour >= 11) & (values.dt.hour < 15)).sum(),
        ),
    )
    tx["demand"] = tx["transaction_count"] / observation_days
    tx["peak_factor"] = tx["peak_transactions"] / tx["transaction_count"]

    result = addresses.merge(metrics, on="location_id", how="inner").merge(
        tx.reset_index(), on="location_id", how="inner"
    )
    if len(result) != len(addresses):
        raise ValueError("Для каждого адреса нужны area_metrics и транзакции")

    competitors = _optional_csv(root, "competitors.csv", ["location_id", "competitors"])
    if competitors is not None:
        result = result.drop(columns=["competitors"], errors="ignore").merge(
            competitors, on="location_id", how="inner"
        )

    property_metrics = _optional_csv(
        root, "property_metrics.csv", ["location_id", "rent_per_sqm", "income_area"]
    )
    if property_metrics is not None:
        result = result.drop(
            columns=["rent_per_sqm", "income_area"], errors="ignore"
        ).merge(property_metrics, on="location_id", how="inner")

    if "rent_cost" not in result:
        if "rent_per_sqm" not in result:
            raise ValueError(
                "Нужна rent_cost в area_metrics.csv или rent_per_sqm в property_metrics.csv"
            )
        low, high = result["rent_per_sqm"].min(), result["rent_per_sqm"].max()
        result["rent_cost"] = 0.5 if high == low else (
            (result["rent_per_sqm"] - low) / (high - low)
        )
    if "income_area" not in result:
        raise ValueError("Нужна income_area в area_metrics.csv или property_metrics.csv")
    if "competitors" not in result:
        raise ValueError("Нужна competitors в area_metrics.csv или competitors.csv")

    result["rent_cost"] = result["rent_cost"].clip(0, 1)
    columns = [
        "lat", "lon", "traffic", "pop_density", "competitors", "avg_check",
        "peak_factor", "income_area", "rent_cost", "demand",
    ]
    result = result[columns].dropna()
    from shapely import contains_xy

    from ml_core.districts import load_district_geometries

    longitudes = result["lon"].to_numpy()
    latitudes = result["lat"].to_numpy()
    inside_city = np.zeros(len(result), dtype=bool)
    for geometry in load_district_geometries():
        inside_city |= contains_xy(geometry, longitudes, latitudes)
    result = result.loc[inside_city]
    if result.empty:
        raise ValueError(
            "После объединения источников не осталось валидных локаций "
            "в районах Санкт-Петербурга"
        )
    return result.reset_index(drop=True)


def _optional_csv(
    data_dir: Path, filename: str, required: list[str]
) -> pd.DataFrame | None:
    path = data_dir / filename
    if not path.is_file():
        return None
    return _read_csv(data_dir, filename, required)
