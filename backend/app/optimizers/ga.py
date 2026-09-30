"""
Agastya Classical Genetic Algorithm (GA) Baseline
Standard elitist genetic algorithm with tournament selection, single-point crossover,
bit-flip mutation, and Pareto archive tracking.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
import numpy as np

from app.optimizers.evaluator import evaluate_fleet_solution
from app.optimizers.pareto import ParetoArchive
from app.constraints.repair import repair_fleet_candidate


class ClassicalGAOptimizer:
    def __init__(
        self,
        problem_spec: Dict[str, Any],
        population_size: int = 40,
        generations: int = 50,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.08,
        seed: int = 42
    ):
        self.problem_spec = problem_spec
        self.population_size = max(10, population_size)
        self.generations = max(5, generations)
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        self.candidate_vessels: List[str] = problem_spec.get(
            "candidate_vessels", ["Container_14000TEU", "Feeder_2500TEU"]
        )
        self.candidate_fuels: List[str] = problem_spec.get(
            "candidate_fuels", ["VLSFO", "LNG", "Methanol", "Ammonia"]
        )
        self.max_fleet_size: int = min(problem_spec.get("max_fleet_size", 30), 60)
        self.min_speed: float = float(problem_spec.get("min_speed_knots", 10.0))
        self.max_speed: float = float(problem_spec.get("max_speed_knots", 22.0))
        self.allow_shore_power: bool = bool(problem_spec.get("allow_shore_power", True))

        self.dim = 5
        self.population = self.rng.uniform(0.0, 1.0, size=(self.population_size, self.dim))
        self.archive = ParetoArchive(max_size=100)

    def _decode_individual(self, ind: np.ndarray) -> Dict[str, Any]:
        p = np.clip(ind, 0.0, 0.9999)
        v_idx = int(p[0] * len(self.candidate_vessels))
        vessel_type = self.candidate_vessels[v_idx]

        v_count = int(1 + p[1] * self.max_fleet_size)
        vessel_count = int(np.clip(v_count, 1, self.max_fleet_size))

        speed_knots = float(np.round(self.min_speed + p[2] * (self.max_speed - self.min_speed), 2))
        f_idx = int(p[3] * len(self.candidate_fuels))
        fuel_type = self.candidate_fuels[f_idx]

        shore_power = bool(p[4] >= 0.5 and self.allow_shore_power)

        return {
            "vessel_type": vessel_type,
            "vessel_count": vessel_count,
            "speed_knots": speed_knots,
            "fuel_type": fuel_type,
            "shore_power_active": shore_power
        }

    def optimize(
        self,
        progress_callback: Optional[Callable[[int, int, List[Dict[str, Any]]], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None
    ) -> List[Dict[str, Any]]:
        for gen in range(1, self.generations + 1):
            if should_cancel and should_cancel():
                break

            current_solutions: List[Dict[str, Any]] = []
            for i in range(self.population_size):
                cand = self._decode_individual(self.population[i])
                repaired, _ = repair_fleet_candidate(
                    candidate=cand,
                    demand=self.problem_spec.get("cargo_demand_teu", 50000),
                    route_distance_nm=self.problem_spec.get("route_distance_nm", 10000),
                    max_delivery_days=self.problem_spec.get("max_delivery_days", 30),
                    emission_cap_tco2e=self.problem_spec.get("emission_cap_tco2e", 100000),
                    origin_port=self.problem_spec.get("origin_port", "CNSHA"),
                    destination_port=self.problem_spec.get("destination_port", "NLRTM"),
                    max_fleet_size=self.max_fleet_size
                )
                evaluated = evaluate_fleet_solution(
                    candidate=repaired,
                    demand=self.problem_spec.get("cargo_demand_teu", 50000),
                    route_distance_nm=self.problem_spec.get("route_distance_nm", 10000),
                    max_delivery_days=self.problem_spec.get("max_delivery_days", 30),
                    emission_cap_tco2e=self.problem_spec.get("emission_cap_tco2e", 100000),
                    carbon_price_usd_per_tco2e=self.problem_spec.get("carbon_price_usd_per_tco2e", 80.0),
                    origin_port=self.problem_spec.get("origin_port", "CNSHA"),
                    destination_port=self.problem_spec.get("destination_port", "NLRTM")
                )
                evaluated["solution_id"] = f"sol_ga_g{gen}_{i+1}"
                current_solutions.append(evaluated)

            self.archive.update(current_solutions)

            # Tournament Selection & Crossover
            next_pop = []
            for _ in range(self.population_size // 2):
                # Tournament
                i1, i2 = self.rng.integers(0, self.population_size, size=2)
                p1 = self.population[i1] if current_solutions[i1]["penalized_cost"] < current_solutions[i2]["penalized_cost"] else self.population[i2]
                i3, i4 = self.rng.integers(0, self.population_size, size=2)
                p2 = self.population[i3] if current_solutions[i3]["penalized_cost"] < current_solutions[i4]["penalized_cost"] else self.population[i4]

                if self.rng.random() < self.crossover_rate:
                    pt = self.rng.integers(1, self.dim)
                    c1 = np.concatenate([p1[:pt], p2[pt:]])
                    c2 = np.concatenate([p2[:pt], p1[pt:]])
                else:
                    c1, c2 = p1.copy(), p2.copy()

                # Mutation
                for c in [c1, c2]:
                    if self.rng.random() < self.mutation_rate:
                        idx = self.rng.integers(0, self.dim)
                        c[idx] = np.clip(c[idx] + self.rng.normal(0.0, 0.15), 0.0, 1.0)
                    next_pop.append(c)

            self.population = np.array(next_pop[:self.population_size])

            if progress_callback:
                progress_callback(gen, self.generations, self.archive.solutions)

        return self.archive.solutions
