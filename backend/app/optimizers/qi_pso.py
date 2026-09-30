"""
Agastya Quantum-Behaved Particle Swarm Optimization (QI-PSO)
Implements delta-potential well dynamics, mean best position (mbest),
stochastic wave-packet collapse, and Pareto archive tracking.
"""

from __future__ import annotations
import copy
from typing import Dict, Any, List, Optional, Callable
import numpy as np

from app.optimizers.evaluator import evaluate_fleet_solution
from app.optimizers.pareto import ParetoArchive, dominates
from app.constraints.repair import repair_fleet_candidate


class QIPSOOptimizer:
    """
    Quantum-Behaved Particle Swarm Optimizer for Multi-Objective Green Fleet Deployment.
    """

    def __init__(
        self,
        problem_spec: Dict[str, Any],
        swarm_size: int = 40,
        iterations: int = 50,
        beta_start: float = 1.0,
        beta_end: float = 0.5,
        seed: int = 42
    ):
        self.problem_spec = problem_spec
        self.swarm_size = max(10, swarm_size)
        self.iterations = max(5, iterations)
        self.beta_start = beta_start
        self.beta_end = beta_end
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

        # Decision dimensions: [vessel_type, vessel_count, speed, fuel_type, shore_power]
        self.dim = 5
        self.positions = self.rng.uniform(0.0, 1.0, size=(self.swarm_size, self.dim))
        self.pbest_positions = self.positions.copy()
        self.pbest_solutions: List[Optional[Dict[str, Any]]] = [None] * self.swarm_size

        self.archive = ParetoArchive(max_size=100)

    def _decode_position(self, pos: np.ndarray) -> Dict[str, Any]:
        """Decodes continuous [0, 1]^5 position vector into discrete fleet variables."""
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

            # 1. Evaluate current particles
            for i in range(self.swarm_size):
                candidate = self._decode_position(self.positions[i])
                repaired, _ = repair_fleet_candidate(
                    candidate=candidate,
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
                evaluated["solution_id"] = f"sol_qipso_it{it}_p{i+1}"
                current_solutions.append(evaluated)

                # Update personal best
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
                    elif not dominates(prev_obj, curr_obj) and self.rng.random() < 0.5:
                        self.pbest_solutions[i] = evaluated
                        self.pbest_positions[i] = self.positions[i].copy()

            # 2. Update Pareto archive
            self.archive.update(current_solutions)

            # 3. Compute mean best position (mbest)
            mbest = np.mean(self.pbest_positions, axis=0)

            # Contraction-expansion coefficient beta
            beta = self.beta_start - (it / self.iterations) * (self.beta_start - self.beta_end)

            # 4. Quantum delta-potential well particle update
            archive_sols = self.archive.solutions
            for i in range(self.swarm_size):
                if archive_sols:
                    gbest_sol = self.rng.choice(archive_sols)
                    gbest_pos = gbest_sol.get("raw_pos", self.pbest_positions[i])
                else:
                    gbest_pos = self.pbest_positions[i]

                for d in range(self.dim):
                    phi = self.rng.uniform(0.0, 1.0)
                    p_id = phi * self.pbest_positions[i, d] + (1.0 - phi) * gbest_pos[d]
                    u = max(1e-6, self.rng.uniform(0.0, 1.0))
                    sign = 1.0 if self.rng.random() > 0.5 else -1.0

                    self.positions[i, d] = np.clip(
                        p_id + sign * beta * np.abs(mbest[d] - self.positions[i, d]) * np.log(1.0 / u),
                        0.0,
                        1.0
                    )

            if progress_callback:
                progress_callback(it, self.iterations, self.archive.solutions)

        return self.archive.solutions
