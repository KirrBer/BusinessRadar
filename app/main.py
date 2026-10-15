from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ml_core.inference import predict_location


class LocationFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float
    lon: float
    traffic: float = Field(ge=0)
    pop_density: float = Field(ge=0)
    competitors: float = Field(ge=0)
    avg_check: float
    peak_factor: float
    income_area: float
    rent_cost: float = Field(ge=0)


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