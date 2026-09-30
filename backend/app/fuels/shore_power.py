"""
Agastya Port Shore Power (Cold Ironing) Dynamics
Calculates berth auxiliary generator emissions versus port electric grid connection.
"""

from __future__ import annotations
from typing import Dict, Any
from app.fuels.fuel_data import fuel_catalog
from app.core.errors import AgastyaValidationError


def calculate_berth_emissions_and_cost(
    port_id: str,
    aux_power_kw: float,
    berth_hours: float,
    use_shore_power: bool = True
) -> Dict[str, Any]:
    """
    Computes emissions and electricity/fuel costs during a port call.
    """
    if aux_power_kw < 0:
        raise AgastyaValidationError(f"Auxiliary power cannot be negative: {aux_power_kw}")
    if berth_hours < 0:
        raise AgastyaValidationError(f"Berth hours cannot be negative: {berth_hours}")

    port = fuel_catalog.get_port(port_id)
    total_kwh = aux_power_kw * berth_hours

    shore_available = bool(port.get("shore_power_available", False))
    grid_ci = float(port.get("grid_carbon_intensity_gco2e_per_kwh", 400.0))
    tariff_kwh = float(port.get("shore_power_tariff_usd_per_kwh", 0.20))
    port_fee = float(port.get("port_fee_per_call_usd", 30000.0))

    if use_shore_power and not shore_available:
        # Graceful fallback: port lacks shore power capability, must use auxiliary diesel generator
        use_shore_power = False
        shore_power_warning = f"Shore power requested but unavailable at {port.get('name', port_id)}. Fell back to auxiliary generator."
    else:
        shore_power_warning = None

    if use_shore_power:
        # Grid powered: emissions = kWh * gCO2e/kWh / 10^6
        emissions_tco2e = (total_kwh * grid_ci) / 1_000_000.0
        energy_cost_usd = total_kwh * tariff_kwh
        source = "shore_grid"
    else:
        # Auxiliary engine on MGO: SFOC ~ 210 g/kWh, TTW + WTT ~ 89.5 gCO2e/MJ
        # 1 kWh = 3.6 MJ -> MGO consumption = total_kwh * 210 g / 10^6 = tonnes
        aux_fuel_tonnes = (total_kwh * 210.0) / 1_000_000.0
        mgo_spec = fuel_catalog.get_fuel("MGO")
        lhv = mgo_spec["lhv_mj_per_kg"]
        total_energy_mj = aux_fuel_tonnes * 1000.0 * lhv
        emissions_tco2e = (total_energy_mj * (mgo_spec["wtt_ghg_gco2e_per_mj"] + mgo_spec["ttw_ghg_gco2e_per_mj"])) / 1_000_000.0
        energy_cost_usd = aux_fuel_tonnes * mgo_spec["default_price_usd_per_tonne"]
        source = "auxiliary_diesel_generator"

    return {
        "port_id": port_id,
        "port_name": port.get("name", port_id),
        "berth_hours": berth_hours,
        "energy_consumed_kwh": round(total_kwh, 1),
        "shore_power_active": use_shore_power,
        "power_source": source,
        "emissions_tco2e": round(emissions_tco2e, 3),
        "energy_cost_usd": round(energy_cost_usd, 2),
        "port_fee_usd": round(port_fee, 2),
        "total_port_cost_usd": round(energy_cost_usd + port_fee, 2),
        "warning": shore_power_warning
    }
