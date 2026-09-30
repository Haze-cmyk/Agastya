"""
Agastya NSGA-II Multi-Objective Genetic Optimizer
Standard NSGA-II implementation with simulated binary crossover (SBX),
polynomial mutation, fast non-dominated sorting, and crowding distance assignment.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
import numpy as np

from app.optimizers.evaluator import evaluate_fleet_solution
from app.optimizers.pareto import (
    ParetoArchive,
    fast_non_dominated_sort,
    calculate_crowding_distance
)
from app.constraints.repair import repair_fleet_candidate


class NSGA2Optimizer:
    """
    NSGA-II multi-objective optimizer.
    """

    def __init__(
        self,
        problem_spec: Dict[str, Any],
        population_size: int = 40,
        generations: int = 50,
        crossover_prob: float = 0.9,
        mutation_prob: float = 0.15,
        seed: int = 42
    ):
        self.problem_spec = problem_spec
        self.population_size = max(10, population_size)
        self.generations = max(5, generations)
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
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

        # Decision vectors in [0, 1]^5
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
            "shore_power_active": shore_power,
            "raw_genome": ind.copy()
        }

    def _sbx_crossover(self, parent1: np.ndarray, parent2: np.ndarray, eta_c: float = 20.0) -> Tuple[np.ndarray, np.ndarray]:
        """Simulated Binary Crossover."""
        if self.rng.random() > self.crossover_prob:
            return parent1.copy(), parent2.copy()

        child1 = np.zeros_like(parent1)
        child2 = np.zeros_like(parent2)

        for i in range(self.dim):
            if self.rng.random() <= 0.5 and abs(parent1[i] - parent2[i]) > 1e-14:
                y1 = min(parent1[i], parent2[i])
                y2 = max(parent1[i], parent2[i])

                rand = self.rng.random()
                beta = 1.0 + (2.0 * (y1 - 0.0) / (y2 - y1))
                alpha = 2.0 - (beta ** -(eta_c + 1.0))
                if rand <= (1.0 / alpha):
                    beta_q = (rand * alpha) ** (1.0 / (eta_c + 1.0))
                else:
                    beta_q = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta_c + 1.0))

                c1 = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))

                beta = 1.0 + (2.0 * (1.0 - y2) / (y2 - y1))
                alpha = 2.0 - (beta ** -(eta_c + 1.0))
                if rand <= (1.0 / alpha):
                    beta_q = (rand * alpha) ** (1.0 / (eta_c + 1.0))
                else:
                    beta_q = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta_c + 1.0))

                c2 = 0.5 * ((y1 + y2) + beta_q * (y2 - y1))

                child1[i] = np.clip(c1, 0.0, 1.0)
                child2[i] = np.clip(c2, 0.0, 1.0)
            else:
                child1[i] = parent1[i]
                child2[i] = parent2[i]

        return child1, child2

    def _polynomial_mutation(self, ind: np.ndarray, eta_m: float = 20.0) -> np.ndarray:
        """Polynomial mutation."""
        mutated = ind.copy()
        for i in range(self.dim):
            if self.rng.random() < self.mutation_prob:
                y = ind[i]
                delta1 = (y - 0.0)
                delta2 = (1.0 - y)
                rand = self.rng.random()
                mut_pow = 1.0 / (eta_m + 1.0)

                if rand < 0.5:
                    xy = 1.0 - delta1
                    val = 2.0 * rand + (1.0 - 2.0 * rand) * (xy ** (eta_m + 1.0))
                    delta_q = val ** mut_pow - 1.0
                else:
                    xy = 1.0 - delta2
                    val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * (xy ** (eta_m + 1.0))
                    delta_q = 1.0 - val ** mut_pow

                mutated[i] = np.clip(y + delta_q, 0.0, 1.0)

        return mutated

    def optimize(
        self,
        progress_callback: Optional[Callable[[int, int, List[Dict[str, Any]]], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None
    ) -> List[Dict[str, Any]]:
        for gen in range(1, self.generations + 1):
            if should_cancel and should_cancel():
                break

            # 1. Generate offspring
            offspring: List[np.ndarray] = []
            while len(offspring) < self.population_size:
                p1_idx = self.rng.integers(0, self.population_size)
                p2_idx = self.rng.integers(0, self.population_size)
                c1, c2 = self._sbx_crossover(self.population[p1_idx], self.population[p2_idx])
                offspring.append(self._polynomial_mutation(c1))
                if len(offspring) < self.population_size:
                    offspring.append(self._polynomial_mutation(c2))

            combined_pop = np.vstack([self.population, np.array(offspring)])

            # 2. Evaluate combined population (size 2N)
            evaluated_list: List[Dict[str, Any]] = []
            for i, ind in enumerate(combined_pop):
                cand = self._decode_individual(ind)
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
                evaluated["solution_id"] = f"sol_nsga2_g{gen}_{i+1}"
                evaluated_list.append(evaluated)

            self.archive.update(evaluated_list)

            # 3. Fast non-dominated sorting and crowding distance survival selection
            objs = np.array([
                [e["penalized_fuel"], e["penalized_cost"], e["penalized_ghg"]]
                for e in evaluated_list
            ], dtype=np.float64)

            fronts = fast_non_dominated_sort(objs)
            new_pop: List[np.ndarray] = []

            for front in fronts:
                if len(new_pop) + len(front) <= self.population_size:
                    for idx in front:
                        new_pop.append(combined_pop[idx])
                else:
                    needed = self.population_size - len(new_pop)
                    distances = calculate_crowding_distance(objs, front)
                    sorted_by_dist = np.argsort(-distances)
                    for k in range(needed):
                        new_pop.append(combined_pop[front[sorted_by_dist[k]]])
                    break

            self.population = np.array(new_pop)

            if progress_callback:
                progress_callback(gen, self.generations, self.archive.solutions)

        return self.archive.solutions
