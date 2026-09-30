"""
Unit tests for fuels catalog, lifecycle Well-to-Wake emissions, methane/N2O slip, and shore power.
"""

import pytest
from app.fuels.fuel_data import fuel_catalog, validate_blend_ratios
from app.fuels.lifecycle import calculate_lifecycle_emissions
from app.fuels.shore_power import calculate_berth_emissions_and_cost
from app.core.errors import AgastyaValidationError


def test_fuel_catalog_retrieval():
    fuels = fuel_catalog.available_fuels
    assert "HFO" in fuels
    assert "VLSFO" in fuels
    assert "LNG" in fuels
    assert "Ammonia" in fuels
    assert "Hydrogen" in fuels


def test_invalid_fuel_name_raises():
    with pytest.raises(AgastyaValidationError):
        fuel_catalog.get_fuel("NonExistentFuel_X")


def test_vlsfo_lifecycle():
    res = calculate_lifecycle_emissions(
        fuel_type="VLSFO",
        fuel_consumed_tonnes=100.0,
        voyage_days=5.0,
        carbon_price_usd_per_tco2e=50.0
    )
    assert res["wtt_ghg_tco2e"] > 0
    assert res["ttw_ghg_tco2e"] > 0
    assert res["total_wtw_ghg_tco2e"] == pytest.approx(res["wtt_ghg_tco2e"] + res["ttw_ghg_tco2e"], rel=1e-2)
    assert res["methane_slip_tco2e"] == 0.0
    assert res["carbon_tax_usd"] > 0.0


def test_lng_methane_slip():
    res = calculate_lifecycle_emissions(
        fuel_type="LNG",
        fuel_consumed_tonnes=100.0,
        voyage_days=5.0
    )
    assert res["methane_slip_tco2e"] > 0.0
    # Pilot fuel MGO must be calculated
    assert res["pilot_fuel_tonnes"] > 0.0
    assert res["pilot_fuel_type"] == "MGO"


def test_ammonia_n2o_slip_and_zero_direct_co2():
    res = calculate_lifecycle_emissions(
        fuel_type="Ammonia",
        fuel_consumed_tonnes=100.0,
        voyage_days=5.0
    )
    assert res["n2o_slip_tco2e"] > 0.0
    # Ammonia itself has 0 ttw CO2 (only pilot MGO contributes direct CO2)
    assert res["wtt_ghg_tco2e"] > 0.0


def test_cryogenic_boil_off():
    res_h2 = calculate_lifecycle_emissions(
        fuel_type="Hydrogen",
        fuel_consumed_tonnes=50.0,
        voyage_days=10.0
    )
    assert res_h2["boil_off_tonnes"] > 0.0


def test_shore_power_at_rotterdam():
    res = calculate_berth_emissions_and_cost(
        port_id="NLRTM",
        aux_power_kw=1500.0,
        berth_hours=24.0,
        use_shore_power=True
    )
    assert res["shore_power_active"] is True
    assert res["power_source"] == "shore_grid"
    assert res["emissions_tco2e"] > 0.0
    assert res["energy_cost_usd"] > 0.0


def test_shore_power_fallback_when_unavailable():
    # Port Hedland (AUPHE) has no shore power
    res = calculate_berth_emissions_and_cost(
        port_id="AUPHE",
        aux_power_kw=1000.0,
        berth_hours=24.0,
        use_shore_power=True
    )
    assert res["shore_power_active"] is False
    assert res["power_source"] == "auxiliary_diesel_generator"
    assert res["warning"] is not None


def test_blend_ratio_validation():
    valid = {"VLSFO": 0.7, "LNG": 0.3}
    normalized = validate_blend_ratios(valid)
    assert sum(normalized.values()) == pytest.approx(1.0, rel=1e-4)

    # Invalid sum: 0.5 != 1.0
    with pytest.raises(AgastyaValidationError):
        validate_blend_ratios({"VLSFO": 0.3, "LNG": 0.2})

    # Negative ratio
    with pytest.raises(AgastyaValidationError):
        validate_blend_ratios({"VLSFO": 1.2, "LNG": -0.2})
