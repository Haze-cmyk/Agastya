"""
Agastya Fuel Prediction and ML Training Endpoints
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
import numpy as np

from app.schemas.schemas import (
    FuelPredictionRequest,
    FuelPredictionResponse,
    TrainPredictorRequest,
    TrainPredictorResponse,
    ModelMetric
)
from app.models.physics import calculate_fuel_consumption
from app.fuels.lifecycle import calculate_lifecycle_emissions
from data.synthetic_generator import generate_telemetry_dataset
from app.models.baselines import train_and_evaluate_all_models
from app.core.errors import AgastyaValidationError

router = APIRouter(prefix="/api/predict", tags=["Fuel Prediction"])


@router.post("", response_model=FuelPredictionResponse)
def predict_vessel_fuel(request: FuelPredictionRequest):
    """
    Computes instant vessel propulsion power, daily fuel consumption rate,
    and lifecycle GHG emissions using hydrodynamic physics.
    """
    try:
        physics_res = calculate_fuel_consumption(
            vessel_type=request.vessel_type,
            speed_knots=request.speed_knots,
            displacement_tonnes=request.displacement_tonnes,
            sea_state_beaufort=request.sea_state_beaufort,
            months_since_drydock=request.months_since_drydock,
            distance_nm=request.distance_nm,
            fuel_type=request.fuel_type
        )

        # Lifecycle GHG calculation if total fuel > 0
        total_fuel = physics_res["total_fuel_tonnes"]
        daily_fuel = physics_res["fuel_consumption_rate_t_per_day"]
        calc_fuel = total_fuel if total_fuel > 0 else daily_fuel

        lifecycle = calculate_lifecycle_emissions(
            fuel_type=request.fuel_type,
            fuel_consumed_tonnes=calc_fuel,
            voyage_days=max(0.1, physics_res["voyage_duration_hours"] / 24.0)
        )

        return FuelPredictionResponse(
            vessel_type=physics_res["vessel_type"],
            speed_knots=physics_res["speed_knots"],
            effective_speed_knots=physics_res["effective_speed_knots"],
            displacement_tonnes=physics_res["displacement_tonnes"],
            engine_power_kw=physics_res["engine_power_kw"],
            engine_load_fraction=physics_res["engine_load_fraction"],
            sfoc_g_per_kwh=physics_res["sfoc_g_per_kwh"],
            fuel_consumption_rate_t_per_day=physics_res["fuel_consumption_rate_t_per_day"],
            total_fuel_tonnes=physics_res["total_fuel_tonnes"],
            voyage_duration_hours=physics_res["voyage_duration_hours"],
            weather_added_resistance_factor=physics_res["weather_added_resistance_factor"],
            fouling_added_resistance_factor=physics_res["fouling_added_resistance_factor"],
            lifecycle_ghg_tco2e=lifecycle["total_wtw_ghg_tco2e"],
            warnings=physics_res["warnings"]
        )

    except AgastyaValidationError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction calculation error: {str(e)}")


@router.post("/train", response_model=TrainPredictorResponse)
def train_and_benchmark_models(request: TrainPredictorRequest):
    """
    Trains and validates Quantum-Inspired Regressor against classical baselines
    (Ridge, Random Forest, Gradient Boosting, MLP) on voyage telemetry.
    """
    try:
        # Generate telemetry
        data = generate_telemetry_dataset(
            sample_count=request.sample_count,
            seed=request.seed,
            vessel_type=request.vessel_type
        )

        if len(data) < 15:
            raise AgastyaValidationError("Insufficient telemetry records for statistical training (< 15 rows).")

        # Feature matrix: [speed_knots, displacement_tonnes, sea_state_beaufort, months_since_drydock]
        X = np.array([
            [r["speed_knots"], r["displacement_tonnes"], r["sea_state_beaufort"], r["months_since_drydock"]]
            for r in data
        ], dtype=np.float64)

        # Target: daily fuel consumption rate (t/day)
        y = np.array([r["fuel_consumption_rate_t_per_day"] for r in data], dtype=np.float64)

        # Train / Validation split (80% / 20%)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        eval_results = train_and_evaluate_all_models(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            seed=request.seed
        )

        metrics_dict = {
            m_name: ModelMetric(**m_vals) for m_name, m_vals in eval_results.items()
        }

        return TrainPredictorResponse(
            sample_count=request.sample_count,
            vessel_type=request.vessel_type,
            models=metrics_dict
        )

    except AgastyaValidationError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training benchmark error: {str(e)}")
