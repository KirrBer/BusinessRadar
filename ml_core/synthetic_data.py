import numpy as np
import pandas as pd
from ml_core.config import RANDOM_STATE

RNG = np.random.default_rng(RANDOM_STATE)

def make_locations(n=6000, n_poles=6, city_bbox=(55.70, 37.50, 55.90, 37.80)):
    lat_min, lon_min, lat_max, lon_max = city_bbox
    lat_c, lon_c = (lat_min + lat_max) / 2, (lon_min + lon_max) / 2

    # 1. Полюса-районы: фиксированные центры активности
    poles_lat = RNG.uniform(lat_min + 0.02, lat_max - 0.02, size=n_poles)
    poles_lon = RNG.uniform(lon_min + 0.02, lon_max - 0.02, size=n_poles)
    pole_income = RNG.normal(1.0, 0.35, size=n_poles)          # статус дохода района
    pole_traffic = RNG.lognormal(6.2, 0.4, size=n_poles)       # «оживлённость» района

    # 2. Каждая локация привязана к своему полюсу -> координаты кластерны
    pole_idx = RNG.integers(0, n_poles, size=n)
    lat = poles_lat[pole_idx] + RNG.normal(0, 0.018, size=n)   # разброс внутри района
    lon = poles_lon[pole_idx] + RNG.normal(0, 0.018, size=n)

    # расстояние локации до СВОЕГО полюса (0 в центре района, растёт к краю)
    d2pole = np.sqrt((lat - poles_lat[pole_idx])**2 + (lon - poles_lon[pole_idx])**2)
    grad = np.exp(-d2pole / 0.03)                              # 1 в центре -> ~0 на краю

    traffic     = pole_traffic[pole_idx] * (0.6 + 0.4 * grad) * RNG.normal(1, 0.15, size=n)
    pop_density = RNG.lognormal(5.2, 0.3, size=n) * (0.5 + 0.5 * grad)
   
    income_area = pole_income[pole_idx] * (0.7 + 0.3 * grad) + RNG.normal(0, 0.12, size=n)
   
    competitors = RNG.poisson(2.0 + 4.0 * grad).astype(float)
    avg_check   = RNG.normal(650, 150, size=n).clip(200, 2000)
    peak_factor = RNG.beta(2, 5, size=n)
    d2center = np.sqrt((lat - lat_c)**2 + (lon - lon_c)**2)
    rent_cost = np.clip(1.2 * np.exp(-d2center / 0.09) + RNG.normal(0, 0.12, size=n), 0.05, 1.0)

 
    base = (0.45*np.log1p(traffic) + 0.25*np.log1p(pop_density) + 0.15*income_area
            + 0.10*peak_factor - 0.20*np.log1p(competitors) + 0.05*avg_check/1000)
    demand = np.exp(base) * RNG.normal(1.0, 0.18, size=n)

    return pd.DataFrame({"lat": lat, "lon": lon, "traffic": traffic,
        "pop_density": pop_density, "competitors": competitors, "avg_check": avg_check,
        "peak_factor": peak_factor, "income_area": income_area,
        "rent_cost": rent_cost, "demand": demand.clip(min=0)})