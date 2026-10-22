from __future__ import annotations
import logging
from ml_core.adapters import (addresses_adapter, geodata_adapter,
                              competitors_adapter, acquiring_adapter, property_adapter)
from ml_core.adapters.base import data_dir, log

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

ADAPTERS = [addresses_adapter, geodata_adapter, competitors_adapter,
            acquiring_adapter, property_adapter]

def build_dataset() -> None:
    log.info("сборка датасета в %s", data_dir())
    for ad in ADAPTERS:                       # порядок не важен: каждый пишет свой CSV
        ad.fetch().pipe(lambda df, n=ad.__name__.split(".")[-1]: None)  # no-op, зовём ниже
    # явный вызов, чтобы каждый адаптер сам записал свой файл через write_csv:
    addresses_adapter.write_csv(addresses_adapter.fetch(), "addresses.csv")
    geodata_adapter.write_csv(geodata_adapter.fetch(), "area_metrics.csv")
    competitors_adapter.write_csv(competitors_adapter.fetch(), "competitors.csv")
    acquiring_adapter.write_csv(acquiring_adapter.fetch(), "transactions.csv")
    property_adapter.write_csv(property_adapter.fetch(), "property_metrics.csv")
    log.info("готово: 5 CSV по схеме data_pipeline -> train без --demo")

if __name__ == "__main__":
    build_dataset()