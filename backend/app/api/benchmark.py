"""
Agastya Benchmark API Controller
Serves precomputed 30-run statistical benchmarks and runs live multi-algorithm comparisons.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
import numpy as np

from app.core.config import BENCHMARKS_DIR
from app.schemas.schemas import BenchmarkRunRequest
from app.optimizers.qiea import QIEAOptimizer
from app.optimizers.qi_pso import QIPSOOptimizer
from app.optimizers.nsga2 import NSGA2Optimizer
from app.optimizers.pareto import compute_normalized_hypervolume, compute_spacing_metric
from app.jobs.job_store import job_store
from app.core.errors import RateLimitExceededError

router = APIRouter(prefix="/api/benchmark", tags=["Benchmarks"])


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.get("/precomputed")
def get_precomputed_benchmarks():
    """
    Returns verified 30-run statistical benchmarks across QIEA, QI-PSO, NSGA-II, GA, and PSO.
    """
    json_path = BENCHMARKS_DIR / "benchmark_results.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark results not found on server.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@router.post("/run")
def run_live_benchmark(body: BenchmarkRunRequest, request: Request):
    """
    Executes live multi-run comparison across selected algorithms with fixed seed.
    """
    client_ip = get_client_ip(request)
    try:
        job_store.check_rate_limit(client_ip)
    except RateLimitExceededError as rle:
        raise HTTPException(status_code=429, detail=str(rle))

    problem_spec = {
        "candidate_vessels": ["Container_14000TEU", "Feeder_2500TEU"],
        "candidate_fuels": ["VLSFO", "LNG", "Methanol", "Ammonia"],
        "cargo_demand_teu": 50000.0,
        "route_distance_nm": 11500.0,
        "max_delivery_days": 28.0,
        "emission_cap_tco2e": 120000.0,
        "carbon_price_usd_per_tco2e": 85.0,
        "max_fleet_size": 20,
        "min_speed_knots": 12.0,
        "max_speed_knots": 22.0,
        "allow_shore_power": True
    }

    results = {}
    for algo in body.algorithms:
        algo_upper = algo.upper()
        hvs = []
        spacings = []
        runtimes = []

        for r in range(body.runs):
            run_seed = body.seed + r * 17
            t0 = time.perf_counter()

            if algo_upper == "QIEA":
                opt = QIEAOptimizer(problem_spec, population_size=20, generations=body.generations, seed=run_seed)
            elif algo_upper in ("QI-PSO", "QIPSO"):
                opt = QIPSOOptimizer(problem_spec, swarm_size=20, iterations=body.generations, seed=run_seed)
            elif algo_upper in ("NSGA-II", "NSGA2"):
                opt = NSGA2Optimizer(problem_spec, population_size=20, generations=body.generations, seed=run_seed)
            else:
                opt = QIEAOptimizer(problem_spec, population_size=20, generations=body.generations, seed=run_seed)

            front = opt.optimize()
            elapsed = time.perf_counter() - t0
            runtimes.append(elapsed)

            if front:
                objs = np.array([
                    [s["fuel_consumption_tonnes"], s["operating_cost_usd"], s["lifecycle_ghg_tco2e"]]
                    for s in front
                ], dtype=np.float64)
                hvs.append(compute_normalized_hypervolume(objs))
                spacings.append(compute_spacing_metric(objs))
            else:
                hvs.append(0.0)
                spacings.append(0.0)

        results[algo] = {
            "hypervolume_mean": round(float(np.mean(hvs)), 3),
            "hypervolume_std": round(float(np.std(hvs)), 3),
            "spacing_mean": round(float(np.mean(spacings)), 2),
            "spacing_std": round(float(np.std(spacings)), 2),
            "runtime_sec_mean": round(float(np.mean(runtimes)), 2),
            "runtime_sec_std": round(float(np.std(runtimes)), 2)
        }

    return {
        "runs": body.runs,
        "generations": body.generations,
        "seed": body.seed,
        "results": results
    }
