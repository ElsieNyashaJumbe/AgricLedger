from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from crop_suitability_model import crop_model


# Create FastAPI application
app = FastAPI(
    title="AgricLedger Crop Suitability API",
    description="API for crop suitability prediction",
    version="1.0.0"
)


# ---------------------------------------------------------
# INPUT DATA
# ---------------------------------------------------------

class WeatherData(BaseModel):
    temperature: float
    rainfall: float
    altitude: float = 500


class ForecastDay(BaseModel):
    avg_temp: float


class CropPredictionRequest(BaseModel):
    location: str
    weather_data: WeatherData
    soil_type: str = "Loam"
    soil_ph: float = 6.5
    forecast_data: Optional[List[ForecastDay]] = None


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "AgricLedger Crop Suitability API is running"
    }


# ---------------------------------------------------------
# PREDICTION
# ---------------------------------------------------------

@app.post("/predict")
def predict(request: CropPredictionRequest):

    try:

        weather_data = request.weather_data.model_dump()

        forecast_data = None

        if request.forecast_data:
            forecast_data = [
                day.model_dump()
                for day in request.forecast_data
            ]

        predictions = crop_model.predict_suitability(
            location=request.location,
            weather_data=weather_data,
            soil_type=request.soil_type,
            soil_ph=request.soil_ph,
            forecast_data=forecast_data
        )

        return {
            "status": "success",
            "predictions": predictions
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )