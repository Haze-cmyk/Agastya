"""
Agastya Solution Evaluator for Fleet Optimization
Computes the 3 Pareto objectives: Total Fuel (t), Operating Cost ($), Lifecycle GHG (tCO2e),
along with constraint validation and penalty adjustments.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import numpy as np

from app.models.physics import calculate_fuel_consumption, vessel_catalog
from app.fuels.lifecycle import calculate_lifecycle_emissions
from app.fuels.shore_power import calculate_berth_emissions_and_cost
from app.constraints.validators import validate_fleet_candidate
from app.constraints.penalty import calculate_constraint_penalties


def evaluate_fleet_solution(
    candidate: Dict[str, Any],
    demand: float,
    route_distance_nm: float,
    max_delivery_days: float,
    emission_cap_tco2e: float,
    carbon_price_usd_per_tco2e: float = 80.0,
    fuel_price_overrides: Optional[Dict[str, float]] = None,
    origin_port: str = "CNSHA",
    destination_port: str = "NLRTM",
    sea_state_beaufort: int = 4,
    months_since_drydock: int = 12
) -> Dict[str, Any]:
    """
    Evaluates a candidate fleet deployment solution.
    """
    vessel_type = candidate.get("vessel_type", "Container_14000TEU")
    vessel_count = int(candidate.get("vessel_count", 1))
    speed_knots = float(candidate.get("speed_knots", 18.0))
    fuel_type = candidate.get("fuel_type", "VLSFO")
    use_shore_power = bool(candidate.get("shore_power_active", True))

    vessel_spec = vessel_catalog.get_vessel(vessel_type)
    unit_cap = float(vessel_spec.get("capacity_value", 10000.0))
    aux_sea_kw = float(vessel_spec.get("auxiliary_power_kw", 2000.0))
    aux_port_kw = float(vessel_spec.get("auxiliary_port_power_kw", 1500.0))

    # Single one-way voyage propulsion
    prop_calc = calculate_fuel_consumption(
        vessel_type=vessel_type,
        speed_knots=speed_knots,
        displacement_tonnes=None,
        sea_state_beaufort=sea_state_beaufort,
        months_since_drydock=months_since_drydock,
        distance_nm=route_distance_nm,
        fuel_type=fuel_type
    )

    effective_speed = prop_calc["effective_speed_knots"]
    transit_hours_oneway = route_distance_nm / max(1.0, effective_speed)
    transit_days_oneway = transit_hours_oneway / 24.0

    # Auxiliary engine fuel at sea (MGO baseline: ~210 g/kWh)
    aux_sea_fuel_t_oneway = (aux_sea_kw * transit_hours_oneway * 210.0) / 1_000_000.0

    # Total one-way voyage fuel (propulsion + auxiliary)
    oneway_fuel_t = prop_calc["total_fuel_tonnes"] + aux_sea_fuel_t_oneway

    # Roundtrip metrics
    roundtrip_transit_days = transit_days_oneway * 2.0
    port_stay_hours_per_roundtrip = 72.0  # Turnaround at both ports
    roundtrip_days = roundtrip_transit_days + (port_stay_hours_per_roundtrip / 24.0)

    # Annual operational metrics (350 operational sailing days / year)
    roundtrips_per_vessel_year = max(1.0, 350.0 / max(1.0, roundtrip_days))
    total_fleet_roundtrips_year = roundtrips_per_vessel_year * vessel_count

    # Annual propulsion + sea auxiliary fuel (tonnes / year)
    annual_sea_fuel_tonnes = oneway_fuel_t * 2.0 * total_fleet_roundtrips_year

    # Fuel lifecycle emissions & costs
    fuel_price = None
    if fuel_price_overrides and fuel_type in fuel_price_overrides:
        fuel_price = fuel_price_overrides[fuel_type]

    lifecycle = calculate_lifecycle_emissions(
        fuel_type=fuel_type,
        fuel_consumed_tonnes=annual_sea_fuel_tonnes,
        voyage_days=roundtrip_days * total_fleet_roundtrips_year,
        carbon_price_usd_per_tco2e=carbon_price_usd_per_tco2e,
        fuel_price_override=fuel_price
    )

    # Port calls and shore power (2 port calls per round trip)
    port_calls_total = int(np.round(total_fleet_roundtrips_year * 2.0))
    berth_eval = calculate_berth_emissions_and_cost(
        port_id=destination_port,
        aux_power_kw=aux_port_kw,
        berth_hours=36.0,
        use_shore_power=use_shore_power
    )
    annual_port_emissions = berth_eval["emissions_tco2e"] * port_calls_total
    annual_port_costs = berth_eval["total_port_cost_usd"] * port_calls_total

    # Fixed OPEX (crew, maintenance, insurance): ~$10,000/day per vessel
    annual_opex = vessel_count * 350.0 * 10500.0

    # Aggregate Objectives
    total_fuel_tonnes = float(np.round(annual_sea_fuel_tonnes, 1))
    total_ghg_tco2e = float(np.round(lifecycle["total_wtw_ghg_tco2e"] + annual_port_emissions, 1))
    total_cost_usd = float(np.round(lifecycle["total_cost_usd"] + annual_port_costs + annual_opex, 1))

    # Preliminary candidate object for constraint checks
    candidate_summary = {
        "vessel_type": vessel_type,
        "vessel_count": vessel_count,
        "speed_knots": effective_speed,
        "fuel_type": fuel_type,
        "shore_power_active": use_shore_power,
        "unit_capacity": unit_cap,
        "fuel_consumption_tonnes": total_fuel_tonnes,
        "operating_cost_usd": total_cost_usd,
        "lifecycle_ghg_tco2e": total_ghg_tco2e,
        "transit_days_oneway": round(transit_days_oneway, 1),
        "annual_fleet_capacity": round(vessel_count * unit_cap * roundtrips_per_vessel_year, 0)
    }

    # Validate constraints
    is_feasible, violations, metrics = validate_fleet_candidate(
        candidate=candidate_summary,
        demand=demand,
        route_distance_nm=route_distance_nm,
        max_delivery_days=max_delivery_days,
        emission_cap_tco2e=emission_cap_tco2e,
        origin_port=origin_port,
        destination_port=destination_port
    )

    # Compute penalties if infeasible
    penalty = 0.0
    if not is_feasible:
        penalty = calculate_constraint_penalties(
            candidate=candidate_summary,
            demand=demand,
            route_distance_nm=route_distance_nm,
            max_delivery_days=max_delivery_days,
            emission_cap_tco2e=emission_cap_tco2e
        )

    # Attach penalty to objectives for optimization ranking
    candidate_summary["feasible"] = is_feasible
    candidate_summary["violations"] = violations
    candidate_summary["penalty"] = round(penalty, 2)
    candidate_summary["metrics"] = metrics

    # Penalized objectives used by metaheuristic search:
    candidate_summary["penalized_fuel"] = total_fuel_tonnes + penalty * 0.1
    candidate_summary["penalized_cost"] = total_cost_usd + penalty * 100.0
    candidate_summary["penalized_ghg"] = total_ghg_tco2e + penalty * 0.2

    return candidate_summary
