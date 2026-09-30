"""
Agastya Classical Particle Swarm Optimization (PSO) Baseline
Standard velocity-position kinematic swarm model with inertia weight decay
and personal/global best attraction.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
import numpy as np

from app.optimizers.evaluator import evaluate_fleet_solution
from app.optimizers.pareto import ParetoArchive, dominates
from app.constraints.repair import repair_fleet_candidate


class ClassicalPSOOptimizer:
    def __init__(
        self,
        problem_spec: Dict[str, Any],
        swarm_size: int = 40,
        iterations: int = 50,
        w_max: float = 0.9,
        w_min: float = 0.4,
        c1: float = 1.5,
        c2: float = 1.5,
        seed: int = 42
    ):
        self.problem_spec = problem_spec
        self.swarm_size = max(10, swarm_size)
        self.iterations = max(5, iterations)
        self.w_max = w_max
        self.w_min = w_min
        self.c1 = c1
        self.c2 = c2
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
        self.positions = self.rng.uniform(0.0, 1.0, size=(self.swarm_size, self.dim))
        self.velocities = self.rng.uniform(-0.1, 0.1, size=(self.swarm_size, self.dim))
        self.pbest_positions = self.positions.copy()
        self.pbest_solutions: List[Optional[Dict[str, Any]]] = [None] * self.swarm_size

        self.archive = ParetoArchive(max_size=100)

    def _decode_position(self, pos: np.ndarray) -> Dict[str, Any]:
        p = np.clip(pos, 0.0, 0.9999)
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
            "raw_pos": pos.copy()
        }

    def optimize(
        self,
        progress_callback: Optional[Callable[[int, int, List[Dict[str, Any]]], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None
    ) -> List[Dict[str, Any]]:
        for it in range(1, self.iterations + 1):
            if should_cancel and should_cancel():
                break

            current_solutions: List[Dict[str, Any]] = []

            for i in range(self.swarm_size):
                cand = self._decode_position(self.positions[i])
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
                evaluated["solution_id"] = f"sol_pso_it{it}_p{i+1}"
                current_solutions.append(evaluated)

                # Personal best update
                if self.pbest_solutions[i] is None:
                    self.pbest_solutions[i] = evaluated
                    self.pbest_positions[i] = self.positions[i].copy()
                else:
                    curr_obj = np.array([evaluated["penalized_fuel"], evaluated["penalized_cost"], evaluated["penalized_ghg"]])
                    prev_obj = np.array([
                        self.pbest_solutions[i]["penalized_fuel"],
                        self.pbest_solutions[i]["penalized_cost"],
                        self.pbest_solutions[i]["penalized_ghg"]
                    ])
                    if dominates(curr_obj, prev_obj):
                        self.pbest_solutions[i] = evaluated
                        self.pbest_positions[i] = self.positions[i].copy()

            self.archive.update(current_solutions)

            # Inertia weight
            w = self.w_max - (it / self.iterations) * (self.w_max - self.w_min)

            # Update swarm kinematics
            archive_sols = self.archive.solutions
            for i in range(self.swarm_size):
                if archive_sols:
                    gbest_sol = self.rng.choice(archive_sols)
                    gbest_pos = gbest_sol.get("raw_pos", self.pbest_positions[i])
                else:
                    gbest_pos = self.pbest_positions[i]

                r1 = self.rng.random(size=self.dim)
                r2 = self.rng.random(size=self.dim)

                self.velocities[i] = (
                    w * self.velocities[i]
                    + self.c1 * r1 * (self.pbest_positions[i] - self.positions[i])
                    + self.c2 * r2 * (gbest_pos - self.positions[i])
                )
                # Clamp velocities
                self.velocities[i] = np.clip(self.velocities[i], -0.2, 0.2)
                self.positions[i] = np.clip(self.positions[i] + self.velocities[i], 0.0, 1.0)

            if progress_callback:
                progress_callback(it, self.iterations, self.archive.solutions)

        return self.archive.solutions
