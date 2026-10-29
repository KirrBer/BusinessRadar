from __future__ import annotations
import datetime as dt
import numpy as np, pandas as pd
from ml_core.adapters._geo_context import all_location_ids, profile
from ml_core.adapters.base import write_csv, log

OBS_DAYS = 90
START = dt.date(2026, 1, 1)

def _sql_bank(engine) -> pd.DataFrame:
    # БОЕВОЙ ПУТЬ — SQL к DWH банка (ClickHouse/Postgres), обезличенные транзакции по эквайрингу.
    # Именно здесь «make_locations просто удаляется и пишется SQL-запрос» из доки.
    SQL = """
        SELECT point_id            AS location_id,
               amount_rur          AS amount,
               transaction_ts      AS transaction_at
        FROM dm.fact_acquiring_tx
        WHERE transaction_ts >= %(start)s
          AND merchant_category IN %(mcc_whitelist)s     # ритейл/HoReCa/услуги
          AND is_anonymized = TRUE
    """
    return pd.read_sql(SQL, engine, params={"start": START, "mcc_whitelist": ("5812", "5411")})

def _mock_transactions(p: dict) -> pd.DataFrame:
    """Разворачивает true_demand/avg_check/peak_factor точки в поштучные транзакции,
    чтобы load_locations, агрегируя, восстановил те же demand/avg_check/peak_factor."""
    rng = np.random.default_rng(hash(p["location_id"]) & 0xFFFFFFFF)
    n = max(int(round(p["true_demand"] * OBS_DAYS)), 1)
    amounts = np.clip(rng.normal(p["avg_check"], p["avg_check"] * .25, n), 50, None)
    days = rng.integers(0, OBS_DAYS, n)
    # доля транзакций в пик-часы (11–15) = peak_factor -> load_locations посчитает его обратно
    in_peak = rng.random(n) < p["peak_factor"]
    hours = np.where(in_peak, rng.integers(11, 15, n), rng.integers(8, 22, n))
    ts = [dt.datetime.combine(START + dt.timedelta(days=int(d)), dt.time(int(h), 0))
          for d, h in zip(days, hours)]
    return pd.DataFrame({"location_id": p["location_id"], "amount": amounts,
                         "transaction_at": ts})

def fetch() -> pd.DataFrame:
    engine = None   # TODO: sqlalchemy.create_engine(BANK_DSN) когда дадут доступ
    if engine is not None:
        log.info("acquiring: читаю реальный DWH банка"); return _sql_bank(engine)
    log.info("acquiring: нет BANK_DSN — разворачиваю стенд-транзакции из профиля")
    return pd.concat([_mock_transactions(profile(i)) for i in all_location_ids()],
                     ignore_index=True)

if __name__ == "__main__":
    write_csv(fetch(), "transactions.csv")