"""
Agastya Fuel Catalog and Validation Services
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import DATA_DIR
from app.core.errors import AgastyaValidationError


class FuelCatalog:
    _instance: Optional[FuelCatalog] = None
    _fuels: Dict[str, Dict[str, Any]] = {}
    _ports: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self._load_data()

    def _load_data(self) -> None:
        fuels_path = DATA_DIR / "fuels.json"
        ports_path = DATA_DIR / "ports.json"

        if fuels_path.exists():
            with open(fuels_path, "r", encoding="utf-8") as f:
                self._fuels = json.load(f)
        if ports_path.exists():
            with open(ports_path, "r", encoding="utf-8") as f:
                self._ports = json.load(f)

    @classmethod
    def get_instance(cls) -> FuelCatalog:
        if cls._instance is None:
            cls._instance = FuelCatalog()
        return cls._instance

    @property
    def available_fuels(self) -> List[str]:
        return list(self._fuels.keys())

    @property
    def available_ports(self) -> List[str]:
        return list(self._ports.keys())

    def get_fuel(self, fuel_name: str) -> Dict[str, Any]:
        normalized = fuel_name.strip()
        if normalized not in self._fuels:
            valid_list = ", ".join(self.available_fuels)
            raise AgastyaValidationError(
                f"Unknown fuel type '{fuel_name}'. Valid options: {valid_list}."
            )
        return self._fuels[normalized]

    def get_port(self, port_id: str) -> Dict[str, Any]:
        normalized = port_id.strip().upper()
        if normalized not in self._ports:
            valid_list = ", ".join(self.available_ports)
            raise AgastyaValidationError(
                f"Unknown port '{port_id}'. Valid options: {valid_list}."
            )
        return self._ports[normalized]

    def is_fuel_available_at_port(self, port_id: str, fuel_name: str) -> bool:
        port = self.get_port(port_id)
        return fuel_name in port.get("available_fuels", [])

    def is_shore_power_available_at_port(self, port_id: str) -> bool:
        port = self.get_port(port_id)
        return bool(port.get("shore_power_available", False))


fuel_catalog = FuelCatalog.get_instance()


def validate_blend_ratios(blend_dict: Dict[str, float]) -> Dict[str, float]:
    """
    Validates that a multi-fuel blend sums to 1.0 (100%) within numerical tolerance.
    Raises AgastyaValidationError if invalid.
    """
    if not blend_dict:
        raise AgastyaValidationError("Fuel blend cannot be empty.")

    total = sum(blend_dict.values())
    if abs(total - 1.0) > 0.01:
        raise AgastyaValidationError(
            f"Fuel blend ratios must sum to 100% (1.0). Current sum: {total * 100.0:.2f}%."
        )

    # Normalize slight rounding differences
    normalized = {}
    for fuel, ratio in blend_dict.items():
        if ratio < 0:
            raise AgastyaValidationError(f"Negative blend ratio for '{fuel}': {ratio}.")
        normalized[fuel] = ratio / total
    return normalized
