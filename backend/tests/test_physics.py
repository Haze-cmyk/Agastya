"""
Unit tests for hydrodynamic propulsion physics, SFOC curves, and environmental drag models.
"""

import pytest
from app.models.physics import calculate_fuel_consumption, vessel_catalog
from app.core.errors import AgastyaValidationError


def test_vessel_catalog_loading():
    vessels = vessel_catalog.available_vessel_types
    assert "Container_14000TEU" in vessels
    assert "Capesize_180000DWT" in vessels
    assert "VLCC_300000DWT" in vessels


def test_nominal_fuel_consumption():
    res = calculate_fuel_consumption(
        vessel_type="Container_14000TEU",
        speed_knots=18.0,
        displacement_tonnes=160000,
        sea_state_beaufort=3,
        months_since_drydock=12,
        distance_nm=3000
    )
    assert res["speed_knots"] == 18.0
    assert res["effective_speed_knots"] == 18.0
    assert res["fuel_consumption_rate_t_per_day"] > 50.0
    assert res["total_fuel_tonnes"] > 0.0
    assert res["voyage_duration_hours"] == pytest.approx(3000 / 18.0, rel=1e-2)
    assert len(res["warnings"]) == 0


def test_speed_exponent_not_hardcoded_cubic():
    spec_container = vessel_catalog.get_vessel("Container_14000TEU")
    spec_bulk = vessel_catalog.get_vessel("Capesize_180000DWT")
    assert spec_container["speed_exponent"] > 3.2
    assert spec_bulk["speed_exponent"] < 3.0


def test_low_speed_clamping_and_warning():
    res = calculate_fuel_consumption(
        vessel_type="Container_14000TEU",
        speed_knots=4.0  # Min speed is 10.0 kn
    )
    assert res["effective_speed_knots"] == 10.0
    assert any("below minimum hydrodynamic" in w for w in res["warnings"])


def test_high_speed_clamping_and_warning():
    res = calculate_fuel_consumption(
        vessel_type="Container_14000TEU",
        speed_knots=28.0  # Max speed is 23.5 kn
    )
    assert res["effective_speed_knots"] == 23.5
    assert any("exceeds rated Maximum Continuous Rating" in w for w in res["warnings"])


def test_zero_speed_safe_handling():
    res = calculate_fuel_consumption(
        vessel_type="Container_14000TEU",
        speed_knots=0.0,
        distance_nm=1000
    )
    assert res["fuel_consumption_rate_t_per_day"] == 0.0
    assert res["total_fuel_tonnes"] == 0.0
    assert res["voyage_duration_hours"] == 0.0
    assert len(res["warnings"]) > 0


def test_extreme_sea_state_clamping():
    res_calm = calculate_fuel_consumption(vessel_type="Container_14000TEU", speed_knots=16.0, sea_state_beaufort=0)
    res_storm = calculate_fuel_consumption(vessel_type="Container_14000TEU", speed_knots=16.0, sea_state_beaufort=10)
    assert res_storm["weather_added_resistance_factor"] <= 2.50
    assert res_storm["fuel_consumption_rate_t_per_day"] > res_calm["fuel_consumption_rate_t_per_day"]
    assert any("Extreme sea state" in w for w in res_storm["warnings"])


def test_heavy_hull_fouling_saturation():
    res_clean = calculate_fuel_consumption(vessel_type="Container_14000TEU", speed_knots=16.0, months_since_drydock=0)
    res_fouled = calculate_fuel_consumption(vessel_type="Container_14000TEU", speed_knots=16.0, months_since_drydock=72)
    assert res_fouled["fouling_added_resistance_factor"] == 1.40
    assert any("Prolonged drydock interval" in w for w in res_fouled["warnings"])


def test_negative_inputs_raise_validation_error():
    with pytest.raises(AgastyaValidationError):
        calculate_fuel_consumption(vessel_type="Container_14000TEU", speed_knots=-10.0)
    with pytest.raises(AgastyaValidationError):
        calculate_fuel_consumption(vessel_type="Container_14000TEU", speed_knots=15.0, sea_state_beaufort=-1)
