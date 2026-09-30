"""
Agastya Constraint Penalty Formulations
Calculates proportional scalar and vector penalties for multi-objective optimization.
"""

from __future__ import annotations
from typing import Dict, Any, List


def calculate_constraint_penalties(
    candidate: Dict[str, Any],
    demand: float,
    route_distance_nm: float,
    max_delivery_days: float,
    emission_cap_tco2e: float
) -> float:
    """
    Computes a composite penalty value for infeasible fleet candidates.
    Returns 0.0 if completely feasible.
    """
    penalty = 0.0

    speed = float(candidate.get("speed_knots", 18.0))
    vessel_count = int(candidate.get("vessel_count", 1))
    unit_cap = float(candidate.get("unit_capacity", 10000.0))

    # Transit time penalty
    transit_hours = route_distance_nm / max(1.0, speed)
    transit_days = transit_hours / 24.0
    if transit_days > max_delivery_days:
        delay = transit_days - max_delivery_days
        penalty += delay * 50000.0

    # Cargo capacity penalty
    roundtrip_days = ((transit_hours * 2.0) + 48.0) / 24.0
    trips_per_year = max(1.0, 350.0 / roundtrip_days)
    delivered = vessel_count * unit_cap * trips_per_year
    if delivered < demand:
        shortfall_fraction = (demand - delivered) / max(1.0, demand)
        penalty += shortfall_fraction * 200000.0

    # Emission cap penalty
    ghg = float(candidate.get("lifecycle_ghg_tco2e", 0.0))
    if emission_cap_tco2e > 0 and ghg > emission_cap_tco2e:
        excess_fraction = (ghg - emission_cap_tco2e) / emission_cap_tco2e
        penalty += excess_fraction * 150000.0

    return penalty
