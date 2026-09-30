"""
Agastya Health and Version Endpoints
"""

from __future__ import annotations
import time
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health & System"])
_server_start_time = time.time()


@router.get("/health")
def health_check():
    """Uptime and readiness ping."""
    return {
        "status": "ok",
        "name": settings.API_TITLE,
        "version": settings.VERSION,
        "uptime_seconds": round(time.time() - _server_start_time, 2),
        "timestamp": time.time()
    }


@router.get("/api/version")
def api_version():
    """API version verification for client compatibility checks."""
    return {
        "name": settings.API_TITLE,
        "version": settings.VERSION,
        "min_client_version": settings.MIN_CLIENT_VERSION
    }
