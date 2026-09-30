"""
Agastya Alternative Fuel Scenario Analyzer API
Evaluates side-by-side fuel economics, carbon pricing sensitivities, and shore power transitions.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import ScenarioCompareRequest, ScenarioCompareResponse
from app.models.physics import calculate_fuel_consumption, vessel_catalog
from app.fuels.lifecycle import calculate_lifecycle_emissions
from app.fuels.shore_power import calculate_berth_emissions_and_cost
from app.fuels.fuel_data import fuel_catalog

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


@router.post("/compare", response_model=ScenarioCompareResponse)
def compare_fuel_scenarios(request: ScenarioCompareRequest):
    """
    Computes comparative metrics across alternative fuels with custom sensitivity adjustments.
    """
    try:
        spec = vessel_catalog.get_vessel(request.vessel_type)
        aux_port_kw = float(spec.get("auxiliary_port_power_kw", 1500.0))

        # Base hydrodynamic propulsion calculation
        prop_calc = calculate_fuel_consumption(
            vessel_type=request.vessel_type,
            speed_knots=request.cruising_speed_knots,
            distance_nm=request.annual_distance_nm
        )

        annual_propulsion_fuel_t = prop_calc["total_fuel_tonnes"]
        sailing_days = prop_calc["voyage_duration_hours"] / 24.0

        fuels_comparison = {}
        available_fuels = fuel_catalog.available_fuels

        # Calculate berth dynamics once
        berth_eval = calculate_berth_emissions_and_cost(
            port_id=request.port_id,
            aux_power_kw=aux_port_kw,
            berth_hours=request.hours_per_port_call,
            use_shore_power=True
        )
        annual_berth_ghg_tco2e = berth_eval["emissions_tco2e"] * request.port_calls_per_year
        annual_berth_cost_usd = berth_eval["total_port_cost_usd"] * request.port_calls_per_year

        # Evaluate each fuel
        for fuel in available_fuels:
            fuel_spec = fuel_catalog.get_fuel(fuel)
            lhv_fuel = fuel_spec["lhv_mj_per_kg"]

            # Energy equivalent fuel consumption based on VLSFO baseline energy
            vlsfo_spec = fuel_catalog.get_fuel("VLSFO")
            baseline_energy_mj = annual_propulsion_fuel_t * 1000.0 * vlsfo_spec["lhv_mj_per_kg"]
            fuel_needed_tonnes = baseline_energy_mj / (1000.0 * lhv_fuel)

            # Price override if provided
            price_override = request.fuel_price_adjustments.get(fuel, fuel_spec["default_price_usd_per_tonne"])

            lifecycle = calculate_lifecycle_emissions(
                fuel_type=fuel,
                fuel_consumed_tonnes=fuel_needed_tonnes,
                voyage_days=sailing_days,
                carbon_price_usd_per_tco2e=request.carbon_price_usd_per_tco2e,
                fuel_price_override=price_override
            )

            total_annual_ghg = lifecycle["total_wtw_ghg_tco2e"] + annual_berth_ghg_tco2e
            total_annual_cost = lifecycle["total_cost_usd"] + annual_berth_cost_usd

            fuels_comparison[fuel] = {
                "fuel_name": fuel_spec["name"],
                "annual_fuel_consumed_tonnes": round(fuel_needed_tonnes, 1),
                "lhv_mj_per_kg": lhv_fuel,
                "wtt_ghg_tco2e": lifecycle["wtt_ghg_tco2e"],
                "ttw_ghg_tco2e": lifecycle["ttw_ghg_tco2e"],
                "methane_slip_tco2e": lifecycle["methane_slip_tco2e"],
                "n2o_slip_tco2e": lifecycle["n2o_slip_tco2e"],
                "boil_off_tonnes": lifecycle["boil_off_tonnes"],
                "berth_ghg_tco2e": round(annual_berth_ghg_tco2e, 1),
                "total_wtw_ghg_tco2e": round(total_annual_ghg, 1),
                "fuel_cost_usd": lifecycle["fuel_cost_usd"],
                "carbon_tax_usd": lifecycle["carbon_tax_usd"],
                "berth_cost_usd": round(annual_berth_cost_usd, 1),
                "total_annual_cost_usd": round(total_annual_cost, 1),
                "requires_cryo_tanks": fuel_spec.get("requires_cryo_tanks", False)
            }

        return ScenarioCompareResponse(
            vessel_type=request.vessel_type,
            annual_distance_nm=request.annual_distance_nm,
            cruising_speed_knots=request.cruising_speed_knots,
            carbon_price_usd_per_tco2e=request.carbon_price_usd_per_tco2e,
            fuels_comparison=fuels_comparison
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario comparison error: {str(e)}")
