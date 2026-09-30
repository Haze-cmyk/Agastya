"""
Unit tests for constraint validators and intelligent repair operator under feasible and infeasible conditions.
"""

import pytest
from app.constraints.validators import validate_fleet_candidate
from app.constraints.repair import repair_fleet_candidate


def test_feasible_fleet_validation():
    candidate = {
        "vessel_type": "Container_14000TEU",
        "vessel_count": 8,
        "speed_knots": 18.0,
        "fuel_type": "VLSFO",
        "shore_power_active": True,
        "lifecycle_ghg_tco2e": 50000.0
    }
    is_feasible, violations, metrics = validate_fleet_candidate(
        candidate=candidate,
        demand=50000.0,
        route_distance_nm=5000.0,
        max_delivery_days=20.0,
        emission_cap_tco2e=100000.0,
        origin_port="CNSHA",
        destination_port="NLRTM"
    )
    assert is_feasible is True
    assert len(violations) == 0
    assert metrics["demand_satisfaction_ratio"] >= 1.0


def test_schedule_deadline_violation():
    candidate = {
        "vessel_type": "Container_14000TEU",
        "vessel_count": 5,
        "speed_knots": 10.0,  # Slow speed takes 500h = 20.8 days
        "fuel_type": "VLSFO",
        "shore_power_active": True
    }
    is_feasible, violations, _ = validate_fleet_candidate(
        candidate=candidate,
        demand=20000.0,
        route_distance_nm=5000.0,
        max_delivery_days=10.0,  # Max 10 days
        emission_cap_tco2e=200000.0
    )
    assert is_feasible is False
    assert any("Schedule reliability breach" in v for v in violations)


def test_port_bunkering_violation():
    candidate = {
        "vessel_type": "Capesize_180000DWT",
        "vessel_count": 4,
        "speed_knots": 13.0,
        "fuel_type": "Hydrogen",  # Not available at Port Hedland (AUPHE)
        "shore_power_active": False
    }
    is_feasible, violations, _ = validate_fleet_candidate(
        candidate=candidate,
        demand=100000.0,
        route_distance_nm=3450.0,
        max_delivery_days=20.0,
        emission_cap_tco2e=200000.0,
        origin_port="AUPHE",
        destination_port="CNSHA"
    )
    assert is_feasible is False
    assert any("Bunkering violation" in v for v in violations)


def test_repair_operator_fixes_demand_and_schedule():
    candidate = {
        "vessel_type": "Container_14000TEU",
        "vessel_count": 1,  # Way too small for 100k TEU
        "speed_knots": 9.0,   # Too slow for 15 days deadline
        "fuel_type": "VLSFO",
        "shore_power_active": True
    }
    repaired, remaining_violations = repair_fleet_candidate(
        candidate=candidate,
        demand=400000.0,
        route_distance_nm=5000.0,
        max_delivery_days=15.0,
        emission_cap_tco2e=300000.0,
        origin_port="CNSHA",
        destination_port="NLRTM",
        max_fleet_size=30
    )
    assert repaired["vessel_count"] > 1
    assert repaired["speed_knots"] >= 13.5
    assert len(remaining_violations) == 0
    assert repaired["feasible"] is True


def test_infeasible_problem_never_crashes():
    """
    Edge case: Absurd demand (100,000,000 TEU) that cannot be met by max_fleet_size (5).
    System must not crash, must return closest candidate with remaining violations.
    """
    candidate = {
        "vessel_type": "Container_14000TEU",
        "vessel_count": 2,
        "speed_knots": 18.0,
        "fuel_type": "VLSFO",
        "shore_power_active": True
    }
    repaired, remaining_violations = repair_fleet_candidate(
        candidate=candidate,
        demand=100_000_000.0,
        route_distance_nm=11500.0,
        max_delivery_days=30.0,
        emission_cap_tco2e=1000.0,  # Unrealistic low emission cap
        origin_port="CNSHA",
        destination_port="NLRTM",
        max_fleet_size=5
    )
    assert repaired is not None
    assert repaired["vessel_count"] == 5
    assert len(remaining_violations) > 0
    assert repaired["feasible"] is False
