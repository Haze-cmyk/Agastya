"""
Agastya Pydantic Request & Response Data Models
Comprehensive boundary constraints, field validation, and error diagnostics.
"""

from __future__ import annotations
import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class FuelPredictionRequest(BaseModel):
    vessel_type: str = Field(default="Container_14000TEU", description="Target vessel class identifier")
    speed_knots: float = Field(default=18.0, ge=0.0, le=45.0, description="Vessel speed through water (knots)")
    displacement_tonnes: Optional[float] = Field(default=None, ge=1000.0, le=600000.0, description="Operational displacement (tonnes)")
    sea_state_beaufort: int = Field(default=3, ge=0, le=12, description="Douglas/Beaufort sea state index (0 to 12)")
    months_since_drydock: int = Field(default=12, ge=0, le=120, description="Months elapsed since last drydock biofouling cleaning")
    distance_nm: Optional[float] = Field(default=None, ge=0.0, le=50000.0, description="Voyage distance in nautical miles")
    fuel_type: str = Field(default="VLSFO", description="Fuel type selection")

    @field_validator("speed_knots")
    @classmethod
    def check_speed_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Speed must be a finite numerical value.")
        return v

    @field_validator("vessel_type", "fuel_type")
    @classmethod
    def check_non_empty_str(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("String identifier cannot be empty.")
        return v.strip()


class FuelPredictionResponse(BaseModel):
    vessel_type: str
    speed_knots: float
    effective_speed_knots: float
    displacement_tonnes: float
    engine_power_kw: float
    engine_load_fraction: float
    sfoc_g_per_kwh: float
    fuel_consumption_rate_t_per_day: float
    total_fuel_tonnes: float
    voyage_duration_hours: float
    weather_added_resistance_factor: float
    fouling_added_resistance_factor: float
    lifecycle_ghg_tco2e: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)


class TrainPredictorRequest(BaseModel):
    data_source: str = Field(default="synthetic", description="'synthetic' or 'custom'")
    sample_count: int = Field(default=300, ge=15, le=5000, description="Number of telemetry samples")
    seed: int = Field(default=42, ge=0, le=1000000)
    vessel_type: str = Field(default="Container_14000TEU")


class ModelMetric(BaseModel):
    rmse: float
    mae: float
    mape: float
    r2: float
    training_time_ms: float


class TrainPredictorResponse(BaseModel):
    sample_count: int
    vessel_type: str
    models: Dict[str, ModelMetric]


class FleetOptimizationRequest(BaseModel):
    algorithm: str = Field(default="QIEA", description="Optimization algorithm (QIEA, QI-PSO, NSGA-II, GA, PSO)")
    preset_id: Optional[str] = Field(default=None, description="Optional case study preset key")
    cargo_demand_teu: float = Field(default=50000.0, gt=0.0, le=10000000.0, description="Required annual cargo demand (TEU or DWT)")
    route_distance_nm: float = Field(default=10000.0, gt=0.0, le=40000.0, description="One-way route nautical miles")
    max_delivery_days: float = Field(default=30.0, gt=0.0, le=180.0, description="Maximum allowable one-way transit days")
    emission_cap_tco2e: float = Field(default=120000.0, ge=0.0, le=10000000.0, description="Annual fleet GHG emission ceiling (tCO2e)")
    carbon_price_usd_per_tco2e: float = Field(default=85.0, ge=0.0, le=1000.0, description="Carbon price tax ($/tCO2e)")
    candidate_vessels: List[str] = Field(default=["Container_14000TEU", "Feeder_2500TEU"], min_length=1)
    candidate_fuels: List[str] = Field(default=["VLSFO", "LNG", "Methanol", "Ammonia"], min_length=1)
    origin_port: str = Field(default="CNSHA")
    destination_port: str = Field(default="NLRTM")
    allow_shore_power: bool = Field(default=True)
    generations: int = Field(default=40, ge=5, le=150)
    population_size: int = Field(default=30, ge=10, le=100)
    seed: int = Field(default=42, ge=0, le=1000000)

    @field_validator("cargo_demand_teu", "route_distance_nm")
    @classmethod
    def check_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Numeric value must be finite.")
        return v


class OptimizationLaunchResponse(BaseModel):
    job_id: str
    algorithm: str
    status: str
    message: str


class OptimizationJobStatusResponse(BaseModel):
    job_id: str
    algorithm: str
    status: str
    progress_percent: float
    current_generation: int
    total_generations: int
    elapsed_seconds: float
    pareto_front: List[Dict[str, Any]]
    hypervolume: float
    spread_metric: float
    error_message: Optional[str] = None


class ScenarioCompareRequest(BaseModel):
    vessel_type: str = Field(default="Container_14000TEU")
    annual_distance_nm: float = Field(default=120000.0, gt=100.0, le=300000.0)
    cruising_speed_knots: float = Field(default=18.0, ge=8.0, le=30.0)
    carbon_price_usd_per_tco2e: float = Field(default=85.0, ge=0.0, le=500.0)
    fuel_price_adjustments: Dict[str, float] = Field(
        default_factory=lambda: {
            "HFO": 550.0,
            "VLSFO": 620.0,
            "MGO": 850.0,
            "LNG": 700.0,
            "Methanol": 650.0,
            "Ammonia": 800.0,
            "Hydrogen": 3500.0
        }
    )
    port_calls_per_year: int = Field(default=24, ge=1, le=150)
    hours_per_port_call: float = Field(default=36.0, ge=4.0, le=120.0)
    shore_power_tariff_usd_per_kwh: float = Field(default=0.20, ge=0.0, le=2.0)
    port_id: str = Field(default="NLRTM")


class ScenarioCompareResponse(BaseModel):
    vessel_type: str
    annual_distance_nm: float
    cruising_speed_knots: float
    carbon_price_usd_per_tco2e: float
    fuels_comparison: Dict[str, Dict[str, Any]]


class BenchmarkRunRequest(BaseModel):
    algorithms: List[str] = Field(default=["QIEA", "QI-PSO", "NSGA-II"], min_length=1)
    runs: int = Field(default=5, ge=1, le=30)
    generations: int = Field(default=25, ge=5, le=50)
    seed: int = Field(default=42)
