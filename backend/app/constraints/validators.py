"""
Agastya Fleet Constraint Validators
Validates cargo demand satisfaction, transit deadlines, port bunkering availability,
shore power compatibility, and greenhouse gas emission caps.
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
from app.fuels.fuel_data import fuel_catalog
from app.models.physics import vessel_catalog


def validate_fleet_candidate(
    candidate: Dict[str, Any],
    demand: float,
    route_distance_nm: float,
    max_delivery_days: float,
    emission_cap_tco2e: float,
    origin_port: str = "CNSHA",
    destination_port: str = "NLRTM"
) -> Tuple[bool, List[str], Dict[str, float]]:
    """
    Checks all operational constraints on a fleet candidate solution.
    Returns: (is_feasible, list_of_violations, metrics_dict)
    """
    violations: List[str] = []
    vessel_type = candidate.get("vessel_type", "Container_14000TEU")
    vessel_count = int(candidate.get("vessel_count", 1))
    speed_knots = float(candidate.get("speed_knots", 18.0))
    fuel_type = candidate.get("fuel_type", "VLSFO")
    use_shore_power = bool(candidate.get("shore_power_active", True))

    vessel_spec = vessel_catalog.get_vessel(vessel_type)
    unit_capacity = float(vessel_spec.get("capacity_value", 10000.0))

    # 1. Schedule & Transit Time
    # Voyage transit hours one-way
    transit_hours = route_distance_nm / max(1.0, speed_knots)
    # Turnaround in port (hours)
    port_hours = 48.0
    total_roundtrip_days = ((transit_hours * 2.0) + port_hours) / 24.0

    if transit_hours / 24.0 > max_delivery_days:
        violations.append(
            f"Schedule reliability breach: Transit time ({transit_hours / 24.0:.1f} days) exceeds maximum delivery deadline ({max_delivery_days:.1f} days)."
        )

    # 2. Annual Capacity & Cargo Demand
    # Roundtrips per vessel per year (assuming 350 operational days/year)
    trips_per_year_per_vessel = max(1.0, 350.0 / total_roundtrip_days)
    total_fleet_capacity = vessel_count * unit_capacity * trips_per_year_per_vessel

    if total_fleet_capacity < demand:
        shortfall = demand - total_fleet_capacity
        violations.append(
            f"Cargo demand unsatisfied: Fleet delivers {total_fleet_capacity:,.0f} units vs required {demand:,.0f} (shortfall: {shortfall:,.0f} units)."
        )

    # 3. Port Fuel Availability
    origin_has_fuel = fuel_catalog.is_fuel_available_at_port(origin_port, fuel_type)
    dest_has_fuel = fuel_catalog.is_fuel_available_at_port(destination_port, fuel_type)
    if not origin_has_fuel:
        violations.append(
            f"Bunkering violation: Selected fuel '{fuel_type}' is unavailable at origin port {origin_port}."
        )
    if not dest_has_fuel:
        violations.append(
            f"Bunkering violation: Selected fuel '{fuel_type}' is unavailable at destination port {destination_port}."
        )

    # 4. Port Shore Power Compatibility
    if use_shore_power:
        if not fuel_catalog.is_shore_power_available_at_port(destination_port):
            violations.append(
                f"Shore power incompatibility: Port {destination_port} does not have cold ironing facilities."
            )

    # 5. Emission Cap (Checked against computed candidate lifecycle GHG)
    candidate_ghg = float(candidate.get("lifecycle_ghg_tco2e", 0.0))
    if emission_cap_tco2e > 0 and candidate_ghg > emission_cap_tco2e:
        excess = candidate_ghg - emission_cap_tco2e
        violations.append(
            f"Emission cap exceeded: Total GHG ({candidate_ghg:,.1f} tCO2e) exceeds cap ({emission_cap_tco2e:,.1f} tCO2e) by {excess:,.1f} tCO2e."
        )

    is_feasible = len(violations) == 0

    metrics = {
        "transit_days": round(transit_hours / 24.0, 2),
        "total_fleet_capacity": round(total_fleet_capacity, 1),
        "annual_roundtrips": round(trips_per_year_per_vessel * vessel_count, 1),
        "demand_satisfaction_ratio": round(total_fleet_capacity / max(1.0, demand), 3)
    }

    return is_feasible, violations, metrics
