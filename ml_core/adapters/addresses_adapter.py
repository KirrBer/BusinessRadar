from __future__ import annotations
import pandas as pd
from ml_core.adapters._geo_context import all_location_ids, profile
from ml_core.adapters.base import write_csv, log

def fetch() -> pd.DataFrame:
    # БОЕВОЙ ПУТЬ (когда дадут доступ к справочнику точек банка):
    #   SELECT location_id, lat, lon FROM dm.ref_open_points WHERE status='ACTIVE'
    #   df = pd.read_sql(SQL, engine_bank)   # SQLAlchemy к DWH
    # В стенде — детерминированный профиль района:
    rows = [profile(i) for i in all_location_ids()]
    return pd.DataFrame(rows)[["location_id", "lat", "lon"]]

if __name__ == "__main__":
    write_csv(fetch(), "addresses.csv")