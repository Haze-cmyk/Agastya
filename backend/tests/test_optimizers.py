"""
Unit tests for multi-objective metaheuristics: QIEA, QI-PSO, NSGA-II, Pareto archives, and Hypervolume metrics.
"""

import numpy as np
import pytest
from app.optimizers.pareto import (
    dominates,
    fast_non_dominated_sort,
    calculate_crowding_distance,
    compute_spacing_metric,
    compute_normalized_hypervolume,
    ParetoArchive
)
from app.optimizers.qiea import QIEAOptimizer
from app.optimizers.qi_pso import QIPSOOptimizer
from app.optimizers.nsga2 import NSGA2Optimizer


def test_pareto_dominance():
    # Minimization
    pt_a = np.array([10.0, 100.0, 50.0])
    pt_b = np.array([12.0, 110.0, 55.0])
    pt_c = np.array([9.0, 120.0, 45.0])

    assert dominates(pt_a, pt_b) is True
    assert dominates(pt_b, pt_a) is False
    assert dominates(pt_a, pt_c) is False
    assert dominates(pt_c, pt_a) is False


def test_fast_non_dominated_sort():
    objs = np.array([
        [10.0, 20.0],
        [12.0, 15.0],
        [15.0, 25.0],
        [8.0, 30.0]
    ])
    fronts = fast_non_dominated_sort(objs)
    # [15.0, 25.0] is dominated by [10, 20] and [12, 15]
    assert 2 not in fronts[0]
    assert 0 in fronts[0]
    assert 1 in fronts[0]
    assert 3 in fronts[0]


def test_spacing_metric_edge_cases():
    # Fewer than 2 points: returns 0.0 without divide by zero
    assert compute_spacing_metric(np.empty((0, 2))) == 0.0
    assert compute_spacing_metric(np.array([[10.0, 20.0]])) == 0.0

    two_pts = np.array([[10.0, 20.0], [12.0, 18.0]])
    assert compute_spacing_metric(two_pts) >= 0.0


def test_hypervolume_metric():
    pts = np.array([
        [0.2, 0.8],
        [0.5, 0.5],
        [0.8, 0.2]
    ])
    hv = compute_normalized_hypervolume(pts)
    assert 0.0 < hv <= 1.0


def test_qiea_optimizer_run():
    spec = {
        "candidate_vessels": ["Container_14000TEU", "Feeder_2500TEU"],
        "candidate_fuels": ["VLSFO", "LNG"],
        "cargo_demand_teu": 30000.0,
        "route_distance_nm": 5000.0,
        "max_delivery_days": 20.0,
        "emission_cap_tco2e": 80000.0,
        "max_fleet_size": 10,
        "min_speed_knots": 12.0,
        "max_speed_knots": 20.0,
        "allow_shore_power": True
    }
    opt = QIEAOptimizer(spec, population_size=15, generations=8, seed=42)
    pareto_front = opt.optimize()

    assert len(pareto_front) > 0
    first_sol = pareto_front[0]
    assert "fuel_consumption_tonnes" in first_sol
    assert "operating_cost_usd" in first_sol
    assert "lifecycle_ghg_tco2e" in first_sol
    assert first_sol["fuel_consumption_tonnes"] > 0


def test_qi_pso_optimizer_run():
    spec = {
        "candidate_vessels": ["Container_14000TEU"],
        "candidate_fuels": ["VLSFO", "LNG"],
        "cargo_demand_teu": 20000.0,
        "route_distance_nm": 4000.0,
        "max_delivery_days": 18.0,
        "emission_cap_tco2e": 50000.0,
        "max_fleet_size": 8,
        "min_speed_knots": 12.0,
        "max_speed_knots": 19.0,
        "allow_shore_power": True
    }
    opt = QIPSOOptimizer(spec, swarm_size=15, iterations=8, seed=42)
    pareto_front = opt.optimize()
    assert len(pareto_front) > 0


def test_nsga2_optimizer_run():
    spec = {
        "candidate_vessels": ["Container_14000TEU"],
        "candidate_fuels": ["VLSFO"],
        "cargo_demand_teu": 20000.0,
        "route_distance_nm": 4000.0,
        "max_delivery_days": 18.0,
        "emission_cap_tco2e": 50000.0,
        "max_fleet_size": 8,
        "min_speed_knots": 12.0,
        "max_speed_knots": 19.0,
        "allow_shore_power": True
    }
    opt = NSGA2Optimizer(spec, population_size=15, generations=8, seed=42)
    pareto_front = opt.optimize()
    assert len(pareto_front) > 0
