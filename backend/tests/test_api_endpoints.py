"""
Integration tests for FastAPI REST API endpoints and error responses.
"""

import pytest


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_api_version(client):
    response = client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"


def test_reference_data_endpoints(client):
    vessels = client.get("/api/data/vessels")
    assert vessels.status_code == 200
    assert "Container_14000TEU" in vessels.json()

    fuels = client.get("/api/data/fuels")
    assert fuels.status_code == 200
    assert "LNG" in fuels.json()

    ports = client.get("/api/data/ports")
    assert ports.status_code == 200
    assert "NLRTM" in ports.json()

    cases = client.get("/api/data/case-studies")
    assert cases.status_code == 200
    assert "asia_europe_container" in cases.json()


def test_predict_endpoint_success(client):
    payload = {
        "vessel_type": "Container_14000TEU",
        "speed_knots": 18.5,
        "sea_state_beaufort": 3,
        "months_since_drydock": 12,
        "fuel_type": "VLSFO",
        "distance_nm": 3000.0
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["fuel_consumption_rate_t_per_day"] > 0
    assert data["total_fuel_tonnes"] > 0
    assert data["engine_power_kw"] > 0


def test_predict_endpoint_validation_error(client):
    # Negative speed triggers 422
    payload = {
        "vessel_type": "Container_14000TEU",
        "speed_knots": -5.0
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "field_errors" in data or "detail" in data


def test_scenario_compare_endpoint(client):
    payload = {
        "vessel_type": "Container_14000TEU",
        "annual_distance_nm": 100000.0,
        "cruising_speed_knots": 18.0,
        "carbon_price_usd_per_tco2e": 85.0
    }
    response = client.post("/api/scenarios/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fuels_comparison" in data
    assert "VLSFO" in data["fuels_comparison"]
    assert "LNG" in data["fuels_comparison"]


def test_benchmark_precomputed_endpoint(client):
    response = client.get("/api/benchmark/precomputed")
    assert response.status_code == 200
    data = response.json()
    assert "solution_quality" in data
    assert "QIEA" in data["solution_quality"]


def test_optimize_and_poll_job_flow(client):
    payload = {
        "algorithm": "QIEA",
        "cargo_demand_teu": 25000.0,
        "route_distance_nm": 4000.0,
        "max_delivery_days": 20.0,
        "emission_cap_tco2e": 50000.0,
        "generations": 5,
        "population_size": 10,
        "seed": 42
    }
    # Launch job
    launch_res = client.post("/api/optimize", json=payload)
    assert launch_res.status_code == 202
    launch_data = launch_res.json()
    job_id = launch_data["job_id"]
    assert job_id.startswith("job_")

    # Poll status
    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ("QUEUED", "RUNNING", "COMPLETED")

    # Cancel job
    cancel_res = client.post(f"/api/jobs/{job_id}/cancel")
    assert cancel_res.status_code == 200


def test_oversized_payload_rejected(client):
    # Create header with Content-Length exceeding 2MB
    huge_headers = {"Content-Length": str(3 * 1024 * 1024)}
    response = client.post("/api/predict", content=b"x", headers=huge_headers)
    assert response.status_code == 413
