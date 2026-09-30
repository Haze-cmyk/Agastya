"""
Agastya Pareto Multi-Objective Optimization Tools
Non-dominated sorting, crowding distance, hypervolume indicator,
spacing/spread metric, and bounded Pareto archive.
"""

from __future__ import annotations
import copy
from typing import List, Dict, Any, Tuple, Optional
import numpy as np


def dominates(obj_a: np.ndarray, obj_b: np.ndarray) -> bool:
    """
    Returns True if obj_a dominates obj_b for minimization.
    obj_a dominates obj_b if obj_a <= obj_b for all objectives and < for at least one.
    """
    all_less_or_equal = np.all(obj_a <= obj_b)
    at_least_one_strict = np.any(obj_a < obj_b)
    return bool(all_less_or_equal and at_least_one_strict)


def fast_non_dominated_sort(objectives: np.ndarray) -> List[List[int]]:
    """
    Deb's Fast Non-Dominated Sorting Algorithm.
    Returns list of fronts, where front[0] is the Pareto-optimal front.
    """
    n = len(objectives)
    if n == 0:
        return []

    domination_sets: List[List[int]] = [[] for _ in range(n)]
    dominated_counts = np.zeros(n, dtype=int)
    fronts: List[List[int]] = [[]]

    for p in range(n):
        for q in range(p + 1, n):
            if dominates(objectives[p], objectives[q]):
                domination_sets[p].append(q)
                dominated_counts[q] += 1
            elif dominates(objectives[q], objectives[p]):
                domination_sets[q].append(p)
                dominated_counts[p] += 1

        if dominated_counts[p] == 0:
            fronts[0].append(p)

    i = 0
    while len(fronts[i]) > 0:
        next_front: List[int] = []
        for p in fronts[i]:
            for q in domination_sets[p]:
                dominated_counts[q] -= 1
                if dominated_counts[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    if not fronts[-1]:
        fronts.pop()

    return fronts


def calculate_crowding_distance(objectives: np.ndarray, front_indices: List[int]) -> np.ndarray:
    """
    Computes crowding distances for solutions in a given Pareto front.
    """
    l = len(front_indices)
    if l == 0:
        return np.array([])
    if l <= 2:
        return np.full(l, np.inf)

    distances = np.zeros(l, dtype=np.float64)
    sub_objs = objectives[front_indices]
    m_objs = sub_objs.shape[1]

    for m in range(m_objs):
        sorted_order = np.argsort(sub_objs[:, m])
        distances[sorted_order[0]] = np.inf
        distances[sorted_order[-1]] = np.inf

        obj_min = sub_objs[sorted_order[0], m]
        obj_max = sub_objs[sorted_order[-1], m]
        spread = obj_max - obj_min
        if spread == 0:
            spread = 1.0

        for i in range(1, l - 1):
            distances[sorted_order[i]] += (
                sub_objs[sorted_order[i + 1], m] - sub_objs[sorted_order[i - 1], m]
            ) / spread

    return distances


def compute_spacing_metric(objectives: np.ndarray) -> float:
    """
    Computes Schott's Spacing (Spread) metric on the Pareto front.
    S = sqrt(1 / (N - 1) * sum((d_i - d_bar)^2))
    Returns 0.0 if front has fewer than 2 distinct points.
    """
    n = len(objectives)
    if n < 2:
        return 0.0

    # Calculate Manhattan distance to nearest neighbor for each solution
    dists = []
    for i in range(n):
        min_d = np.inf
        for j in range(n):
            if i != j:
                d = np.sum(np.abs(objectives[i] - objectives[j]))
                if d < min_d:
                    min_d = d
        dists.append(min_d)

    dists_arr = np.array(dists)
    d_bar = np.mean(dists_arr)
    variance = np.sum((dists_arr - d_bar) ** 2) / (n - 1)
    return float(np.sqrt(variance))


def compute_hypervolume_2d(points: np.ndarray, ref_point: np.ndarray) -> float:
    """Computes exact 2D hypervolume bounded by ref_point."""
    if len(points) == 0:
        return 0.0
    # Filter points dominating the reference point
    valid = points[np.all(points <= ref_point, axis=1)]
    if len(valid) == 0:
        return 0.0

    # Sort by first objective ascending
    sorted_pts = valid[np.argsort(valid[:, 0])]
    # Remove dominated points internally
    non_dom = [sorted_pts[0]]
    for pt in sorted_pts[1:]:
        if pt[1] < non_dom[-1][1]:
            non_dom.append(pt)

    non_dom = np.array(non_dom)
    hv = 0.0
    prev_x = non_dom[0, 0]
    for i in range(len(non_dom)):
        x_i = non_dom[i, 0]
        y_i = non_dom[i, 1]
        width = ref_point[0] - x_i
        height = ref_point[1] - y_i if i == 0 else non_dom[i - 1, 1] - y_i
        hv += width * height
    return float(hv)


def compute_normalized_hypervolume(objectives: np.ndarray, ref_multiplier: float = 1.1) -> float:
    """
    Computes normalized hypervolume (in [0, 1]) for 2D or 3D objective vectors.
    """
    if len(objectives) == 0:
        return 0.0
    if len(objectives) == 1:
        return 0.50

    objs = np.asarray(objectives, dtype=np.float64)
    min_bounds = np.min(objs, axis=0)
    max_bounds = np.max(objs, axis=0)
    ranges = max_bounds - min_bounds
    ranges = np.where(ranges < 1e-6, 1.0, ranges)

    # Normalize to [0, 1]
    norm_objs = (objs - min_bounds) / ranges
    ref_point = np.ones(objs.shape[1]) * ref_multiplier

    if objs.shape[1] == 2:
        hv = compute_hypervolume_2d(norm_objs, ref_point)
        max_possible_hv = ref_multiplier * ref_multiplier
        return round(float(np.clip(hv / max_possible_hv, 0.0, 1.0)), 3)
    else:
        # Monte-Carlo approximation for 3D normalized hypervolume
        n_samples = 5000
        rng = np.random.default_rng(42)
        samples = rng.uniform(0.0, ref_multiplier, size=(n_samples, objs.shape[1]))
        # A sample is dominated if any norm_obj <= sample
        dominated_count = 0
        for sample in samples:
            if np.any(np.all(norm_objs <= sample, axis=1)):
                dominated_count += 1
        hv = dominated_count / n_samples
        return round(float(hv), 3)


class ParetoArchive:
    """Bounded Pareto Archive maintaining non-dominated solutions."""
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.solutions: List[Dict[str, Any]] = []

    def update(self, new_solutions: List[Dict[str, Any]]) -> None:
        candidates = self.solutions + new_solutions
        if not candidates:
            return

        objs = np.array([
            [sol["fuel_consumption_tonnes"], sol["operating_cost_usd"], sol["lifecycle_ghg_tco2e"]]
            for sol in candidates
        ], dtype=np.float64)

        fronts = fast_non_dominated_sort(objs)
        if not fronts or not fronts[0]:
            return

        first_front_indices = fronts[0]
        # Keep non-dominated solutions
        non_dom_solutions = [candidates[i] for i in first_front_indices]

        # Truncate using crowding distance if exceeds max_size
        if len(non_dom_solutions) > self.max_size:
            front_objs = objs[first_front_indices]
            distances = calculate_crowding_distance(front_objs, list(range(len(first_front_indices))))
            sorted_by_crowding = np.argsort(-distances)
            non_dom_solutions = [non_dom_solutions[i] for i in sorted_by_crowding[:self.max_size]]

        self.solutions = non_dom_solutions

    def get_objectives_matrix(self) -> np.ndarray:
        if not self.solutions:
            return np.empty((0, 3))
        return np.array([
            [sol["fuel_consumption_tonnes"], sol["operating_cost_usd"], sol["lifecycle_ghg_tco2e"]]
            for sol in self.solutions
        ], dtype=np.float64)
