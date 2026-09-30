"""
Agastya Reference Data Endpoints
Serves reference databases for vessels, fuels, ports, and case studies.
"""

from __future__ import annotations
import json
from fastapi import APIRouter
from app.core.config import DATA_DIR

router = APIRouter(prefix="/api/data", tags=["Reference Data"])


@router.get("/vessels")
def get_vessels():
    with open(DATA_DIR / "vessels.json", "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/fuels")
def get_fuels():
    with open(DATA_DIR / "fuels.json", "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/ports")
def get_ports():
    with open(DATA_DIR / "ports.json", "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/case-studies")
def get_case_studies():
    with open(DATA_DIR / "case_studies.json", "r", encoding="utf-8") as f:
        return json.load(f)
