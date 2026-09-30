# Agastya: API Reference

All requests and responses use standard `application/json` payloads. Base path: `/api`.

---

## 1. System & Health

### `GET /health`
Uptime health check endpoint.
- **Response**: `200 OK`
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-09-30T10:30:00Z",
  "uptime_seconds": 1245.8
}
```

### `GET /api/version`
API version compatibility check.
- **Response**: `200 OK`
```json
{
  "name": "Agastya API",
  "version": "1.0.0",
  "min_client_version": "1.0.0"
}
```

---

## 2. Fuel Prediction

### `POST /api/predict`
Calculates instant vessel fuel consumption and emissions using hydrodynamic physics and quantum-inspired regressor models.
- **Request Body**:
```json
{
  "vessel_type": "Container_14000TEU",
  "speed_knots": 18.5,
  "displacement_tonnes": 165000,
  "sea_state_beaufort": 4,
  "months_since_drydock": 12,
  "fuel_type": "VLSFO",
  "distance_nm": 3200
}
```
- **Response**: `200 OK`
```json
{
  "speed_knots": 18.5,
  "engine_power_kw": 48250.0,
  "engine_load_fraction": 0.74,
  "sfoc_g_per_kwh": 168.5,
  "fuel_consumption_rate_t_per_day": 195.12,
  "total_fuel_tonnes": 1409.2,
  "ghg_ttw_tonnes": 4446.0,
  "ghg_wtw_tonnes": 5122.5,
  "warnings": []
}
```

### `POST /api/predict/train`
Trains and benchmarks the Quantum-Inspired Regressor against classical baselines (Linear Regression, Random Forest, Gradient Boosting, ANN) using uploaded or synthetic telemetry.
- **Request Body**:
```json
{
  "data_source": "synthetic",
  "sample_count": 250,
  "random_seed": 42
}
```
- **Response**: `200 OK`
```json
{
  "sample_count": 250,
  "models": {
    "qi_regressor": { "rmse": 4.12, "mae": 3.05, "mape": 3.82, "r2": 0.981, "training_time_ms": 42.1 },
    "random_forest": { "rmse": 4.85, "mae": 3.42, "mape": 4.15, "r2": 0.974, "training_time_ms": 112.5 },
    "gradient_boosting": { "rmse": 4.31, "mae": 3.18, "mape": 3.95, "r2": 0.979, "training_time_ms": 86.4 },
    "linear_regression": { "rmse": 9.24, "mae": 7.15, "mape": 8.92, "r2": 0.902, "training_time_ms": 2.1 },
    "ann": { "rmse": 4.60, "mae": 3.33, "mape": 4.02, "r2": 0.976, "training_time_ms": 145.0 }
  }
}
```

---

## 3. Fleet Optimization

### `POST /api/optimize`
Launches an asynchronous fleet optimization run.
- **Request Body**:
```json
{
  "algorithm": "QIEA",
  "preset_id": "asia_europe_container",
  "cargo_demand_teu": 45000,
  "route_distance_nm": 11500,
  "max_delivery_days": 30.0,
  "emission_cap_tco2e": 60000.0,
  "carbon_price_per_tonne": 85.0,
  "candidate_vessels": ["Container_14000TEU", "Feeder_2500TEU"],
  "candidate_fuels": ["VLSFO", "LNG", "Methanol", "Ammonia"],
  "allow_shore_power": true,
  "generations": 50,
  "population_size": 40,
  "seed": 42
}
```
- **Response**: `202 Accepted`
```json
{
  "job_id": "job_948f2b71",
  "status": "QUEUED",
  "message": "Optimization job scheduled"
}
```

### `GET /api/jobs/{id}`
Polls progress, status, and partial/final Pareto front for an optimization job.
- **Response**: `200 OK`
```json
{
  "job_id": "job_948f2b71",
  "status": "COMPLETED",
  "progress_percent": 100.0,
  "current_generation": 50,
  "total_generations": 50,
  "elapsed_seconds": 6.84,
  "pareto_front": [
    {
      "solution_id": "sol_1",
      "vessel_count": 4,
      "vessel_type": "Container_14000TEU",
      "speed_knots": 17.2,
      "fuel_type": "LNG",
      "shore_power_active": true,
      "fuel_consumption_tonnes": 14210.5,
      "operating_cost_usd": 12850400.0,
      "lifecycle_ghg_tco2e": 41200.3,
      "feasible": true,
      "violations": []
    }
  ],
  "hypervolume": 0.842,
  "spread_metric": 0.185
}
```

### `POST /api/jobs/{id}/cancel`
Cancels an ongoing job immediately.
- **Response**: `200 OK`
```json
{
  "job_id": "job_948f2b71",
  "status": "CANCELLED"
}
```

---

## 4. Alternative Fuel Scenarios

### `POST /api/scenarios/compare`
Synchronous comparison across fuel types with sensitivity parameter controls.
- **Request Body**:
```json
{
  "vessel_type": "Container_14000TEU",
  "annual_distance_nm": 120000,
  "cruising_speed_knots": 18.0,
  "carbon_price_usd_per_tco2e": 100.0,
  "fuel_prices_usd_per_tonne": {
    "HFO": 550.0,
    "VLSFO": 620.0,
    "MGO": 850.0,
    "LNG": 700.0,
    "Methanol": 650.0,
    "Ammonia": 800.0,
    "Hydrogen": 3500.0
  },
  "shore_power_tariff_usd_per_kwh": 0.18,
  "port_calls_per_year": 24,
  "hours_per_port_call": 36
}
```

---

## 5. Benchmarks

### `GET /api/benchmark/precomputed`
Returns saved statistical benchmarks over 30 independent runs with fixed seeds across QIEA, QI-PSO, NSGA-II, classical GA, and classical PSO.

### `POST /api/benchmark/run`
Runs live comparative benchmark test.
- **Request Body**:
```json
{
  "algorithms": ["QIEA", "QI-PSO", "NSGA-II"],
  "fleet_sizes": [5, 15, 30],
  "runs": 5,
  "seed": 1001
}
```

---

## 6. Reference Data Endpoints

- `GET /api/data/vessels`: Vessel displacement, design speed, cargo capacity, power ratings.
- `GET /api/data/fuels`: Fuel Lower Heating Value (MJ/kg), carbon densities, slip factors, boil-off rates.
- `GET /api/data/ports`: Global ports with coordinates, fuel bunkering availability, shore power readiness.
