"""
Agastya Intelligent Constraint Repair Operator
Heuristically repairs infeasible fleet configurations to maintain solution feasibility.
Never crashes on fundamentally infeasible problems; returns closest candidate with violation log.
"""

from __future__ import annotations
import copy
import math
from typing import Dict, Any, List, Tuple
import numpy as np
from app.fuels.fuel_data import fuel_catalog
from app.models.physics import vessel_catalog
from app.constraints.validators import validate_fleet_candidate


def repair_fleet_candidate(
    candidate: Dict[str, Any],
    demand: float,
    route_distance_nm: float,
    max_delivery_days: float,
    emission_cap_tco2e: float,
    origin_port: str = "CNSHA",
    destination_port: str = "NLRTM",
    max_fleet_size: int = 50
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Applies heuristic repair passes to satisfy operational constraints.
    Returns: (repaired_candidate, remaining_violations)
    """
    repaired = copy.deepcopy(candidate)
    vessel_type = repaired.get("vessel_type", "Container_14000TEU")
    spec = vessel_catalog.get_vessel(vessel_type)

    v_min = spec["min_speed_knots"]
    v_max = spec["max_speed_knots"]
    unit_cap = float(spec.get("capacity_value", 10000.0))

    # --- Pass 1: Port compatibility & Fuel Availability ---
    current_fuel = repaired.get("fuel_type", "VLSFO")
    origin_has_fuel = fuel_catalog.is_fuel_available_at_port(origin_port, current_fuel)
    dest_has_fuel = fuel_catalog.is_fuel_available_at_port(destination_port, current_fuel)

    if not (origin_has_fuel and dest_has_fuel):
        # Find intersection of available fuels
        origin_fuels = set(fuel_catalog.get_port(origin_port).get("available_fuels", []))
        dest_fuels = set(fuel_catalog.get_port(destination_port).get("available_fuels", []))
        common_fuels = list(origin_fuels.intersection(dest_fuels))

        if common_fuels:
            # Prefer cleaner common fuels: Ammonia -> Methanol -> LNG -> VLSFO -> HFO
            priority = ["Ammonia", "Methanol", "LNG", "MGO", "VLSFO", "HFO"]
            chosen = next((f for f in priority if f in common_fuels), common_fuels[0])
            repaired["fuel_type"] = chosen
        else:
            # Fallback to standard bunker
            repaired["fuel_type"] = "VLSFO"

    # --- Pass 2: Shore Power Availability ---
    if repaired.get("shore_power_active", False):
        if not fuel_catalog.is_shore_power_available_at_port(destination_port):
            repaired["shore_power_active"] = False

    # --- Pass 3: Schedule Deadline Repair ---
    current_speed = float(repaired.get("speed_knots", 18.0))
    transit_hours = route_distance_nm / max(1.0, current_speed)
    transit_days = transit_hours / 24.0

    if transit_days > max_delivery_days:
        # Minimum speed needed: route_distance_nm / (max_delivery_days * 24)
        min_required_speed = route_distance_nm / (max_delivery_days * 24.0)
        repaired["speed_knots"] = float(min(min_required_speed * 1.02, v_max))

    # --- Pass 4: Cargo Demand & Fleet Sizing Repair ---
    vessel_count = int(repaired.get("vessel_count", 1))
    speed = float(repaired.get("speed_knots", 18.0))
    roundtrip_days = ((route_distance_nm * 2.0 / max(1.0, speed)) + 48.0) / 24.0
    trips_per_vessel = max(1.0, 350.0 / roundtrip_days)
    capacity_per_vessel = unit_cap * trips_per_vessel

    current_fleet_capacity = vessel_count * capacity_per_vessel
    if current_fleet_capacity < demand:
        # Calculate needed vessels
        needed_vessels = int(np.ceil(demand / max(1.0, capacity_per_vessel)))
        repaired["vessel_count"] = min(needed_vessels, max_fleet_size)

    # Final check of feasibility
    is_feasible, remaining_violations, _ = validate_fleet_candidate(
        repaired,
        demand=demand,
        route_distance_nm=route_distance_nm,
        max_delivery_days=max_delivery_days,
        emission_cap_tco2e=emission_cap_tco2e,
        origin_port=origin_port,
        destination_port=destination_port
    )

    repaired["feasible"] = is_feasible
    repaired["violations"] = remaining_violations

    return repaired, remaining_violations
