from __future__ import annotations
import hashlib
import numpy as np
from ml_core.config import RANDOM_STATE

N_POINTS = 1500
_POLES = 6
_BBOX = (59.88, 30.20, 60.05, 30.50)          # СПб, как в границах районов из README

def _poles():
    rng = np.random.default_rng(RANDOM_STATE)
    lat = rng.uniform(_BBOX[0] + .02, _BBOX[2] - .02, _POLES)
    lon = rng.uniform(_BBOX[1] + .02, _BBOX[3] - .02, _POLES)
    return lat, lon, rng.normal(1.0, .35, _POLES), rng.lognormal(6.2, .4, _POLES)

PLAT, PLON, PINC, PTRAF = _poles()
_CENTROID = ((_BBOX[0] + _BBOX[2]) / 2, (_BBOX[1] + _BBOX[3]) / 2)

def all_location_ids() -> list[str]:
    return [f"LOC{i:06d}" for i in range(N_POINTS)]

def _idx(location_id: str) -> int:
    return int(location_id[3:])

def _rng_for(location_id: str) -> np.random.Generator:
    # стабильный rng ТОЧКИ независимо от порядка вызовов/процессов
    seed = (RANDOM_STATE * 1_000_003 + _idx(location_id)) & 0xFFFFFFFF
    return np.random.default_rng(seed)

def profile(location_id: str) -> dict:
    i = _idx(location_id); rng = _rng_for(location_id)
    pole = i % _POLES
    lat = PLAT[pole] + rng.normal(0, .012)
    lon = PLON[pole] + rng.normal(0, .012)
    d2p = np.hypot(lat - PLAT[pole], lon - PLON[pole]); grad = np.exp(-d2p / .03)
    traffic = PTRAF[pole] * (.6 + .4 * grad) * rng.normal(1, .08)
    pop = np.exp(rng.normal(5.2, .3)) * (.5 + .5 * grad)
    income = PINC[pole] * (.7 + .3 * grad) + rng.normal(0, .06)
    comps = float(rng.poisson(2.0 + 4.0 * grad))
    d2c = np.hypot(lat - _CENTROID[0], lon - _CENTROID[1])
    rent = float(np.clip(1.2 * np.exp(-d2c / .09) + rng.normal(0, .12), .05, 1.0))
    avg_check = float(np.clip(rng.normal(650, 150), 200, 2000))
    peak = float(rng.beta(2, 5))
    base = (.45*np.log1p(traffic) + .25*np.log1p(pop) + .15*income
            + .10*peak - .20*np.log1p(comps) + .05*avg_check/1000)
    true_demand = float(np.exp(base) * rng.normal(1.0, .12))   # шум меньше, чем в make_locations
    return dict(location_id=location_id, lat=lat, lon=lon, traffic=traffic,
                pop_density=pop, competitors=comps, rent_per_sqm=rent,
                income_area=income, avg_check=avg_check, peak_factor=peak,
                true_demand=max(true_demand, 1e-3))