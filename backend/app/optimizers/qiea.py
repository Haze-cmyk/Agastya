"""
Agastya Quantum-Inspired Evolutionary Algorithm (QIEA)
Employs Q-bit representation, quantum rotation gates U(Delta theta),
H-epsilon catastrophe operator, and multi-objective Pareto front tracking.
"""

from __future__ import annotations
import copy
from typing import Dict, Any, List, Optional, Callable
import numpy as np

from app.optimizers.evaluator import evaluate_fleet_solution
from app.optimizers.pareto import ParetoArchive, fast_non_dominated_sort, calculate_crowding_distance
from app.constraints.repair import repair_fleet_candidate


class QIEAOptimizer:
    """
    Quantum-Inspired Evolutionary Algorithm for multi-objective fleet optimization.
    """

    def __init__(
        self,
        problem_spec: Dict[str, Any],
        population_size: int = 40,
        generations: int = 50,
        rotation_angle: float = 0.05 * np.pi,
        catastrophe_threshold: float = 0.08,
        seed: int = 42
    ):
        self.problem_spec = problem_spec
        self.population_size = max(10, population_size)
        self.generations = max(5, generations)
        self.rotation_angle = rotation_angle
        self.catastrophe_threshold = catastrophe_threshold
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

        # Chromosome bit length:
        # 3 bits for vessel type (up to 8 types)
        # 6 bits for vessel count (1 to 64)
        # 6 bits for speed quantization (64 levels between min_speed and max_speed)
        # 3 bits for fuel type (up to 8 fuels)
        # 1 bit for shore power
        self.bit_lengths = [3, 6, 6, 3, 1]
        self.total_bits = sum(self.bit_lengths)

        # Initialize Q-bit population: angles initialized to pi / 4 (maximum superposition |alpha|^2 = |beta|^2 = 0.5)
        self.theta_pop = np.full((self.population_size, self.total_bits), np.pi / 4.0, dtype=np.float64)

        self.archive = ParetoArchive(max_size=100)

    def _collapse_chromosome(self, theta_individual: np.ndarray) -> np.ndarray:
        """Observes Q-bits and collapses to binary state."""
        beta_squared = np.sin(theta_individual) ** 2
        rand_vals = self.rng.random(size=self.total_bits)
        binary_bits = (rand_vals < beta_squared).astype(int)
        return binary_bits

    def _decode_binary(self, bits: np.ndarray) -> Dict[str, Any]:
        """Decodes binary string into operational fleet deployment decisions."""
        idx = 0

        # 1. Vessel Type
        b_vessel = bits[idx : idx + self.bit_lengths[0]]
        vessel_int = int("".join(map(str, b_vessel)), 2) % len(self.candidate_vessels)
        vessel_type = self.candidate_vessels[vessel_int]
        idx += self.bit_lengths[0]

        # 2. Vessel Count (1 to max_fleet_size)
        b_count = bits[idx : idx + self.bit_lengths[1]]
        count_int = int("".join(map(str, b_count)), 2)
        vessel_count = int(np.clip((count_int % self.max_fleet_size) + 1, 1, self.max_fleet_size))
        idx += self.bit_lengths[1]

        # 3. Speed Knots
        b_speed = bits[idx : idx + self.bit_lengths[2]]
        speed_int = int("".join(map(str, b_speed)), 2)
        max_levels = 2 ** self.bit_lengths[2] - 1
        speed_fraction = speed_int / max_levels
        speed_knots = float(np.round(self.min_speed + speed_fraction * (self.max_speed - self.min_speed), 2))
        idx += self.bit_lengths[2]

        # 4. Fuel Type
        b_fuel = bits[idx : idx + self.bit_lengths[3]]
        fuel_int = int("".join(map(str, b_fuel)), 2) % len(self.candidate_fuels)
        fuel_type = self.candidate_fuels[fuel_int]
        idx += self.bit_lengths[3]

        # 5. Shore Power
        shore_power_active = bool(bits[idx] == 1 and self.allow_shore_power)

        return {
            "vessel_type": vessel_type,
            "vessel_count": vessel_count,
            "speed_knots": speed_knots,
            "fuel_type": fuel_type,
            "shore_power_active": shore_power_active,
            "raw_bits": bits
        }

    def _update_qbits(
        self,
        theta_individual: np.ndarray,
        binary_individual: np.ndarray,
        best_binary: np.ndarray
    ) -> np.ndarray:
        """
        Applies quantum rotation gate U(Delta theta) steering towards best solution.
        """
        updated_theta = theta_individual.copy()
        for j in range(self.total_bits):
            curr_bit = binary_individual[j]
            best_bit = best_binary[j]

            # Rotation direction table
            if curr_bit == 0 and best_bit == 1:
                delta = self.rotation_angle
            elif curr_bit == 1 and best_bit == 0:
                delta = -self.rotation_angle
            else:
                delta = 0.0

            # Rotate phase angle
            new_angle = updated_theta[j] + delta
            # Bound within [0.01 * pi, 0.49 * pi] to avoid irreversible zero collapse
            updated_theta[j] = np.clip(new_angle, 0.01 * np.pi, 0.49 * np.pi)

        return updated_theta

    def _check_and_apply_catastrophe(self) -> None:
        """
        H-epsilon catastrophe operator: detects loss of angle diversity and resets toward pi/4.
        """
        angle_std = np.std(self.theta_pop)
        if angle_std < self.catastrophe_threshold:
            # Catastrophe triggered: perturb 30% of population towards pi/4
            reset_count = int(self.population_size * 0.35)
            reset_indices = self.rng.choice(self.population_size, size=reset_count, replace=False)
            for idx in reset_indices:
                noise = self.rng.normal(0.0, 0.05, size=self.total_bits)
                self.theta_pop[idx] = np.clip(np.pi / 4.0 + noise, 0.02 * np.pi, 0.48 * np.pi)

    def optimize(
        self,
        progress_callback: Optional[Callable[[int, int, List[Dict[str, Any]]], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes multi-objective QIEA optimization loop.
        """
        for gen in range(1, self.generations + 1):
            if should_cancel and should_cancel():
                break

            current_solutions: List[Dict[str, Any]] = []
            observed_bits_list: List[np.ndarray] = []

            # 1. Quantum state collapse and solution generation
            for i in range(self.population_size):
                bits = self._collapse_chromosome(self.theta_pop[i])
                candidate = self._decode_binary(bits)

                # Heuristic repair pass
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

                # Evaluate candidate
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

                evaluated["solution_id"] = f"sol_qiea_g{gen}_i{i+1}"
                current_solutions.append(evaluated)
                observed_bits_list.append(bits)

            # 2. Update Pareto archive
            self.archive.update(current_solutions)

            # 3. Select non-dominated guide solutions for quantum rotation gates
            archive_sols = self.archive.solutions
            if archive_sols:
                for i in range(self.population_size):
                    guide = self.rng.choice(archive_sols)
                    guide_bits = guide.get("raw_bits", observed_bits_list[0])
                    self.theta_pop[i] = self._update_qbits(
                        self.theta_pop[i], observed_bits_list[i], guide_bits
                    )

            # 4. Diversity maintenance / catastrophe operator
            self._check_and_apply_catastrophe()

            if progress_callback:
                progress_callback(gen, self.generations, self.archive.solutions)

        return self.archive.solutions
