"""
Agastya Lifecycle Well-to-Wake (WTW) Emissions Calculator
Accounts for WTT upstream, TTW combustion, dual-fuel pilot injections,
methane slip (GWP 28), N2O slip (GWP 273), and cryogenic boil-off gas.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from app.fuels.fuel_data import fuel_catalog
from app.core.errors import AgastyaValidationError


GWP_CH4_100YR = 28.0
GWP_N2O_100YR = 273.0


def calculate_lifecycle_emissions(
    fuel_type: str,
    fuel_consumed_tonnes: float,
    voyage_days: float = 1.0,
    carbon_price_usd_per_tco2e: float = 0.0,
    fuel_price_override: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes complete Well-to-Wake greenhouse gas emissions and operational costs.
    """
    if fuel_consumed_tonnes < 0:
        raise AgastyaValidationError(f"Fuel consumption cannot be negative: {fuel_consumed_tonnes}")
    if voyage_days < 0:
        raise AgastyaValidationError(f"Voyage days cannot be negative: {voyage_days}")

    fuel_spec = fuel_catalog.get_fuel(fuel_type)
    lhv = fuel_spec["lhv_mj_per_kg"]
    wtt_factor = fuel_spec["wtt_ghg_gco2e_per_mj"]
    ttw_factor = fuel_spec["ttw_ghg_gco2e_per_mj"]
    price_per_t = fuel_price_override if fuel_price_override is not None else fuel_spec["default_price_usd_per_tonne"]

    # Handle dual-fuel pilot fuel requirement
    pilot_fraction = fuel_spec.get("pilot_fuel_fraction", 0.0)
    pilot_fuel_type = fuel_spec.get("pilot_fuel_type")

    main_fuel_tonnes = fuel_consumed_tonnes * (1.0 - pilot_fraction)
    pilot_fuel_tonnes = fuel_consumed_tonnes * pilot_fraction

    # Main fuel energy in MJ: tonnes * 1000 kg/t * LHV MJ/kg
    main_energy_mj = main_fuel_tonnes * 1000.0 * lhv

    # Main fuel WTT & TTW in tCO2e: energy (MJ) * factor (gCO2e/MJ) / 10^6
    main_wtt_tco2e = (main_energy_mj * wtt_factor) / 1_000_000.0
    main_ttw_tco2e = (main_energy_mj * ttw_factor) / 1_000_000.0

    # Pilot fuel emissions
    pilot_wtt_tco2e = 0.0
    pilot_ttw_tco2e = 0.0
    pilot_cost_usd = 0.0
    if pilot_fuel_tonnes > 0 and pilot_fuel_type:
        pilot_spec = fuel_catalog.get_fuel(pilot_fuel_type)
        p_energy_mj = pilot_fuel_tonnes * 1000.0 * pilot_spec["lhv_mj_per_kg"]
        pilot_wtt_tco2e = (p_energy_mj * pilot_spec["wtt_ghg_gco2e_per_mj"]) / 1_000_000.0
        pilot_ttw_tco2e = (p_energy_mj * pilot_spec["ttw_ghg_gco2e_per_mj"]) / 1_000_000.0
        pilot_cost_usd = pilot_fuel_tonnes * pilot_spec["default_price_usd_per_tonne"]

    # Methane slip penalty (LNG)
    methane_slip_frac = fuel_spec.get("methane_slip_fraction", 0.0)
    slip_ch4_tonnes = main_fuel_tonnes * methane_slip_frac
    slip_ch4_tco2e = slip_ch4_tonnes * GWP_CH4_100YR

    # N2O slip penalty (Ammonia)
    n2o_slip_frac = fuel_spec.get("n2o_slip_fraction", 0.0)
    slip_n2o_tonnes = main_fuel_tonnes * n2o_slip_frac
    slip_n2o_tco2e = slip_n2o_tonnes * GWP_N2O_100YR

    total_slip_tco2e = slip_ch4_tco2e + slip_n2o_tco2e

    # Cryogenic Boil-Off Gas (BOG)
    bog_rate = fuel_spec.get("daily_boil_off_fraction", 0.0)
    # Estimated bunker reserve is at least 1.1x consumption
    bunker_reserve_t = fuel_consumed_tonnes * 1.15
    bog_tonnes = bunker_reserve_t * bog_rate * voyage_days
    # Boil-off fugitive emissions if not captured
    bog_energy_mj = bog_tonnes * 1000.0 * lhv
    bog_wtt_tco2e = (bog_energy_mj * wtt_factor) / 1_000_000.0

    # Total Well-to-Wake GHG
    total_wtt = main_wtt_tco2e + pilot_wtt_tco2e + bog_wtt_tco2e
    total_ttw = main_ttw_tco2e + pilot_ttw_tco2e + total_slip_tco2e
    total_wtw = total_wtt + total_ttw

    # Costs
    main_fuel_cost_usd = main_fuel_tonnes * price_per_t
    bog_loss_cost_usd = bog_tonnes * price_per_t
    fuel_purchase_cost_usd = main_fuel_cost_usd + pilot_cost_usd + bog_loss_cost_usd
    carbon_tax_cost_usd = total_wtw * max(0.0, carbon_price_usd_per_tco2e)
    total_operational_cost_usd = fuel_purchase_cost_usd + carbon_tax_cost_usd

    return {
        "fuel_type": fuel_type,
        "fuel_consumed_tonnes": round(fuel_consumed_tonnes, 2),
        "main_fuel_tonnes": round(main_fuel_tonnes, 2),
        "pilot_fuel_tonnes": round(pilot_fuel_tonnes, 2),
        "pilot_fuel_type": pilot_fuel_type,
        "boil_off_tonnes": round(bog_tonnes, 3),
        "wtt_ghg_tco2e": round(total_wtt, 2),
        "ttw_ghg_tco2e": round(total_ttw, 2),
        "methane_slip_tco2e": round(slip_ch4_tco2e, 2),
        "n2o_slip_tco2e": round(slip_n2o_tco2e, 2),
        "total_wtw_ghg_tco2e": round(total_wtw, 2),
        "fuel_cost_usd": round(fuel_purchase_cost_usd, 2),
        "carbon_tax_usd": round(carbon_tax_cost_usd, 2),
        "total_cost_usd": round(total_operational_cost_usd, 2)
    }
