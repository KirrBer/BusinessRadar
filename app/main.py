from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ml_core.config import demo_mode_enabled
from ml_core.data_pipeline import load_locations
from ml_core.districts import district_feature_collection
from ml_core.inference import predict_location
from ml_core.synthetic_data import make_locations


class LocationFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90, description="Широта в градусах")
    lon: float = Field(ge=-180, le=180, description="Долгота в градусах")
    traffic: float = Field(
        ge=0,
        description="Условное число потенциальных посетителей в день",
    )
    pop_density: float = Field(
        ge=0,
        description="Плотность населения, человек на км²",
    )
    competitors: float = Field(
        ge=0,
        description="Условное число конкурентов в зоне анализа",
    )
    avg_check: float = Field(ge=0, description="Средний чек в рублях")
    peak_factor: float = Field(
        ge=0,
        le=1,
        description="Доля пикового спроса, от 0 до 1",
    )
    income_area: float = Field(
        description="Индекс дохода района относительно среднего: 1.0 = средний",
    )
    rent_cost: float = Field(
        ge=0,
        le=1,
        description="Нормализованный индекс аренды: 0 = низкая, 1 = высокая",
    )


class PredictionResponse(BaseModel):
    score: int
    demand_forecast: float
    demand_percentile: float
    cluster_id: int
    cluster_name: str
    recommendation_text: str


app = FastAPI(title="BusinessRadar API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/districts")
def districts() -> dict:
    locations = make_locations() if demo_mode_enabled() else load_locations()
    return district_feature_collection(locations)


@app.post("/api/v1/predict", response_model=PredictionResponse)
def predict(features: LocationFeatures) -> PredictionResponse:
    try:
        return predict_location(features.model_dump())
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="ML artifacts are unavailable; train the models first.",
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error