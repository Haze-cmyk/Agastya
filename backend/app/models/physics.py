"""
Agastya Hydrodynamic Propulsion and Fuel Consumption Physics Engine
Computes vessel propulsion power, part-load SFOC, weather added resistance,
and hull biofouling degradation with rigorous boundary guards.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from app.core.config import DATA_DIR
from app.core.errors import AgastyaValidationError


class VesselCatalog:
    _instance: Optional[VesselCatalog] = None
    _vessels: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        vessels_path = DATA_DIR / "vessels.json"
        if vessels_path.exists():
            with open(vessels_path, "r", encoding="utf-8") as f:
                self._vessels = json.load(f)

    @classmethod
    def get_instance(cls) -> VesselCatalog:
        if cls._instance is None:
            cls._instance = VesselCatalog()
        return cls._instance

    @property
    def available_vessel_types(self) -> List[str]:
        return list(self._vessels.keys())

    def get_vessel(self, vessel_type: str) -> Dict[str, Any]:
        if vessel_type not in self._vessels:
            types_str = ", ".join(self.available_vessel_types)
            raise AgastyaValidationError(
                f"Unknown vessel type '{vessel_type}'. Available options: {types_str}."
            )
        return self._vessels[vessel_type]


vessel_catalog = VesselCatalog.get_instance()


def calculate_fuel_consumption(
    vessel_type: str,
    speed_knots: float,
    displacement_tonnes: Optional[float] = None,
    sea_state_beaufort: int = 3,
    months_since_drydock: int = 12,
    distance_nm: Optional[float] = None,
    fuel_type: str = "VLSFO"
) -> Dict[str, Any]:
    """
    Computes instantaneous propulsion power, daily fuel consumption rate,
    and total voyage fuel with boundary clamping and warning flags.
    """
    warnings: List[str] = []

    # Validate inputs
    if speed_knots < 0:
        raise AgastyaValidationError(f"Vessel speed cannot be negative: {speed_knots} kn")
    if displacement_tonnes is not None and displacement_tonnes < 0:
        raise AgastyaValidationError(f"Displacement cannot be negative: {displacement_tonnes} t")
    if sea_state_beaufort < 0:
        raise AgastyaValidationError(f"Sea state cannot be negative: {sea_state_beaufort}")
    if months_since_drydock < 0:
        raise AgastyaValidationError(f"Months since drydock cannot be negative: {months_since_drydock}")

    spec = vessel_catalog.get_vessel(vessel_type)
    v_min = spec["min_speed_knots"]
    v_max = spec["max_speed_knots"]
    disp_design = spec["displacement_design_tonnes"]
    disp_light = spec["displacement_light_tonnes"]
    mcr_kw = spec["engine_mcr_kw"]
    n_exp = spec["speed_exponent"]
    c_hull = spec["c_hull"]
    base_sfoc = spec["base_sfoc_g_per_kwh"]

    # Effective displacement
    if displacement_tonnes is None:
        effective_disp = disp_design * 0.85
    else:
        # Clamp displacement between light ballast and 110% design
        if displacement_tonnes < disp_light:
            warnings.append(
                f"Displacement ({displacement_tonnes}t) is below light ballast ({disp_light}t). Clamped to light displacement."
            )
            effective_disp = disp_light
        elif displacement_tonnes > disp_design * 1.15:
            warnings.append(
                f"Displacement ({displacement_tonnes}t) exceeds maximum structural limit. Clamped to 115% design displacement."
            )
            effective_disp = disp_design * 1.15
        else:
            effective_disp = displacement_tonnes

    # Edge-case speed handling: zero speed
    if speed_knots == 0.0:
        return {
            "vessel_type": vessel_type,
            "speed_knots": 0.0,
            "effective_speed_knots": 0.0,
            "engine_power_kw": 0.0,
            "engine_load_fraction": 0.0,
            "sfoc_g_per_kwh": base_sfoc,
            "fuel_consumption_rate_t_per_day": 0.0,
            "total_fuel_tonnes": 0.0,
            "voyage_duration_hours": 0.0,
            "weather_added_resistance_factor": 1.0,
            "fouling_added_resistance_factor": 1.0,
            "warnings": ["Vessel is stationary (speed = 0). Propulsion fuel is 0."]
        }

    # Speed clamping
    effective_speed = speed_knots
    if speed_knots < v_min:
        warnings.append(
            f"Speed ({speed_knots:.1f} kn) is below minimum hydrodynamic maneuvering limit ({v_min:.1f} kn). Clamped to {v_min:.1f} kn."
        )
        effective_speed = v_min
    elif speed_knots > v_max:
        warnings.append(
            f"Speed ({speed_knots:.1f} kn) exceeds rated Maximum Continuous Rating hull limit ({v_max:.1f} kn). Clamped to {v_max:.1f} kn."
        )
        effective_speed = v_max

    # Sea state added resistance (Beaufort 0-12)
    clamped_beaufort = min(sea_state_beaufort, 12)
    if sea_state_beaufort > 8:
        warnings.append(
            f"Extreme sea state (Beaufort {sea_state_beaufort} - storm/hurricane force). Non-linear wave resistance capped at 2.50x."
        )
        weather_factor = min(1.0 + 0.0085 * (clamped_beaufort ** 2) + 0.05 * ((clamped_beaufort - 7) ** 3), 2.50)
    else:
        weather_factor = 1.0 + 0.0085 * (clamped_beaufort ** 2)

    # Hull biofouling factor
    if months_since_drydock > 60:
        warnings.append(
            f"Prolonged drydock interval ({months_since_drydock} months). Biofouling resistance saturated at +40%."
        )
        fouling_factor = 1.40
    else:
        fouling_factor = 1.0 + 0.14 * ((months_since_drydock / 60.0) ** 1.4)

    # Calm water propulsion power (kW)
    # Admiralty power relation: P = c_hull * (disp / disp_design)^(2/3) * v^n
    p_calm = c_hull * ((effective_disp / disp_design) ** (2.0 / 3.0)) * (effective_speed ** n_exp)

    # Total operational propulsion power (kW)
    prop_power = p_calm * weather_factor * fouling_factor

    # Cap power at 108% MCR (engine governor overload trip)
    if prop_power > mcr_kw * 1.08:
        warnings.append(
            f"Requested speed requires {prop_power:.0f} kW, exceeding rated engine MCR ({mcr_kw} kW). Clamped to governor overload limit."
        )
        prop_power = mcr_kw * 1.08

    # Engine load fraction L = P / P_MCR
    engine_load = prop_power / max(1.0, mcr_kw)

    # SFOC curve: bathtub/parabolic with low-load penalty
    # Optimal load at 75% MCR
    sfoc_penalty = 0.35 * ((engine_load - 0.75) ** 2)
    if engine_load < 0.30:
        sfoc_penalty += 0.25 * (0.30 - engine_load)
        warnings.append(
            f"Engine operating at low load ({engine_load * 100.0:.1f}% MCR). Specific fuel consumption penalty applied."
        )

    sfoc = base_sfoc * (1.0 + sfoc_penalty)

    # Daily fuel consumption rate (tonnes / day)
    # m_dot = (P [kW] * SFOC [g/kWh] * 24 h) / 10^6 g/t
    daily_fuel_t = (prop_power * sfoc * 24.0) / 1_000_000.0

    # Voyage calculations if distance provided
    voyage_hours = 0.0
    total_fuel_t = 0.0
    if distance_nm is not None and distance_nm > 0:
        voyage_hours = distance_nm / effective_speed
        total_fuel_t = (prop_power * sfoc * voyage_hours) / 1_000_000.0

    return {
        "vessel_type": vessel_type,
        "speed_knots": round(speed_knots, 2),
        "effective_speed_knots": round(effective_speed, 2),
        "displacement_tonnes": round(effective_disp, 1),
        "engine_power_kw": round(prop_power, 1),
        "engine_load_fraction": round(engine_load, 3),
        "sfoc_g_per_kwh": round(sfoc, 2),
        "fuel_consumption_rate_t_per_day": round(daily_fuel_t, 2),
        "total_fuel_tonnes": round(total_fuel_t, 2),
        "voyage_duration_hours": round(voyage_hours, 2),
        "weather_added_resistance_factor": round(weather_factor, 3),
        "fouling_added_resistance_factor": round(fouling_factor, 3),
        "warnings": warnings
    }
