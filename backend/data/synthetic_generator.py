"""
Agastya Synthetic Voyage Telemetry Generator
Generates realistic vessel operational data according to hydrodynamic physics
with sensor noise, engine load fluctuations, and weather perturbations.
"""

from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

DATA_DIR = Path(__file__).resolve().parent


def load_vessels() -> Dict[str, Any]:
    with open(DATA_DIR / "vessels.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_fuels() -> Dict[str, Any]:
    with open(DATA_DIR / "fuels.json", "r", encoding="utf-8") as f:
        return json.load(f)


def generate_telemetry_dataset(
    sample_count: int = 500,
    seed: int = 42,
    vessel_type: str = "Container_14000TEU"
) -> List[Dict[str, Any]]:
    """
    Generates synthetic noon-report telemetry records for a vessel type.
    """
    rng = np.random.default_rng(seed)
    vessels = load_vessels()
    if vessel_type not in vessels:
        vessel_type = "Container_14000TEU"

    spec = vessels[vessel_type]
    v_min = spec["min_speed_knots"]
    v_max = spec["max_speed_knots"]
    disp_light = spec["displacement_light_tonnes"]
    disp_design = spec["displacement_design_tonnes"]
    n_exp = spec["speed_exponent"]
    c_hull = spec["c_hull"]
    mcr_kw = spec["engine_mcr_kw"]
    base_sfoc = spec["base_sfoc_g_per_kwh"]

    records = []
    for i in range(sample_count):
        # Operational speed in knots
        speed = float(np.round(rng.uniform(v_min, v_max), 2))
        # Cargo load fraction (0.3 to 1.0)
        load_fraction = float(np.round(rng.uniform(0.35, 1.0), 3))
        displacement = disp_light + load_fraction * (disp_design - disp_light)

        # Environmental sea state (Beaufort 0 to 8)
        # Most days are Beaufort 2-5, occasionally severe
        beaufort = int(np.clip(np.round(rng.exponential(scale=2.8)), 0, 8))

        # Months since drydock (0 to 60)
        months_fouling = int(rng.integers(0, 50))

        # Weather resistance factor: 1 + 0.008 * B^2
        weather_factor = 1.0 + 0.0085 * (beaufort ** 2)

        # Fouling factor: 1 + 0.15 * (months / 60)^1.4
        fouling_factor = 1.0 + 0.14 * ((months_fouling / 60.0) ** 1.4)

        # Baseline calm water propulsion power (kW)
        p_calm = c_hull * ((displacement / disp_design) ** (2.0 / 3.0)) * (speed ** n_exp)
        prop_power = float(np.clip(p_calm * weather_factor * fouling_factor, 100.0, mcr_kw * 1.08))

        # Engine load fraction
        engine_load = prop_power / mcr_kw

        # SFOC curve: parabolic with low-load penalty
        sfoc_penalty = 0.35 * ((engine_load - 0.75) ** 2)
        if engine_load < 0.35:
            sfoc_penalty += 0.20 * (0.35 - engine_load)
        sfoc = float(base_sfoc * (1.0 + sfoc_penalty))

        # Fuel consumption rate in tonnes/day (main engine)
        daily_fuel_t = (prop_power * sfoc * 24.0) / 1_000_000.0

        # Add 3% Gaussian sensor noise and occasional mild sensor disturbance
        noise = float(rng.normal(1.0, 0.03))
        daily_fuel_noisy = float(np.round(np.clip(daily_fuel_t * noise, 5.0, 400.0), 2))

        # Voyage segment distance (nm over 24h)
        segment_distance_nm = float(np.round(speed * 24.0 * rng.uniform(0.96, 1.02), 1))

        records.append({
            "report_id": f"NOON_{i+1:04d}",
            "vessel_type": vessel_type,
            "speed_knots": speed,
            "displacement_tonnes": float(np.round(displacement, 1)),
            "load_fraction": load_fraction,
            "sea_state_beaufort": beaufort,
            "months_since_drydock": months_fouling,
            "engine_power_kw": float(np.round(prop_power, 1)),
            "engine_load_fraction": float(np.round(engine_load, 3)),
            "sfoc_g_per_kwh": float(np.round(sfoc, 2)),
            "fuel_consumption_rate_t_per_day": daily_fuel_noisy,
            "distance_run_24h_nm": segment_distance_nm,
            "fuel_type": "VLSFO"
        })

    return records


def export_sample_csv(target_file: Path | str, count: int = 250) -> None:
    data = generate_telemetry_dataset(sample_count=count)
    if not data:
        return
    keys = list(data[0].keys())
    with open(target_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)


def export_sample_fleet_csv(target_file: Path | str) -> None:
    fleet_rows = [
        {"vessel_name": "Agastya Voyager", "vessel_type": "Container_14000TEU", "built_year": 2021, "current_fuel": "VLSFO", "capacity_teu": 14000, "assigned_speed_knots": 17.5},
        {"vessel_name": "Agastya Pioneer", "vessel_type": "Container_14000TEU", "built_year": 2022, "current_fuel": "LNG", "capacity_teu": 14000, "assigned_speed_knots": 18.0},
        {"vessel_name": "Agastya Feeder 1", "vessel_type": "Feeder_2500TEU", "built_year": 2018, "current_fuel": "MGO", "capacity_teu": 2500, "assigned_speed_knots": 15.0},
        {"vessel_name": "Agastya Feeder 2", "vessel_type": "Feeder_2500TEU", "built_year": 2019, "current_fuel": "Methanol", "capacity_teu": 2500, "assigned_speed_knots": 15.5},
        {"vessel_name": "Agastya Iron 1", "vessel_type": "Capesize_180000DWT", "built_year": 2020, "current_fuel": "VLSFO", "capacity_dwt": 180000, "assigned_speed_knots": 13.0},
        {"vessel_name": "Agastya Iron 2", "vessel_type": "Capesize_180000DWT", "built_year": 2023, "current_fuel": "LNG", "capacity_dwt": 180000, "assigned_speed_knots": 13.5},
        {"vessel_name": "Agastya Trader", "vessel_type": "Panamax_82000DWT", "built_year": 2017, "current_fuel": "VLSFO", "capacity_dwt": 82000, "assigned_speed_knots": 13.0},
        {"vessel_name": "Agastya Neptune", "vessel_type": "VLCC_300000DWT", "built_year": 2021, "current_fuel": "VLSFO", "capacity_dwt": 300000, "assigned_speed_knots": 14.5},
        {"vessel_name": "Agastya Energy", "vessel_type": "Aframax_115000DWT", "built_year": 2022, "current_fuel": "LNG", "capacity_dwt": 115000, "assigned_speed_knots": 14.0}
    ]
    fieldnames = ["vessel_name", "vessel_type", "built_year", "current_fuel", "capacity_teu", "capacity_dwt", "assigned_speed_knots"]
    with open(target_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
        writer.writeheader()
        writer.writerows(fleet_rows)


if __name__ == "__main__":
    export_sample_csv(DATA_DIR / "sample_telemetry.csv", 300)
    export_sample_fleet_csv(DATA_DIR / "sample_fleet.csv")
    print("Exported sample telemetry and fleet CSVs.")
