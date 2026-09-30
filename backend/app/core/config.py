"""
Agastya Application Configuration
Loads environment variables with robust defaults for local development and cloud deployment.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_ROOT / "data"
BENCHMARKS_DIR = BACKEND_ROOT / "benchmarks"


class Settings:
    PROJECT_NAME: str = "Agastya — Quantum-Inspired Green Fleet Optimizer"
    API_TITLE: str = "Agastya API"
    VERSION: str = "1.0.0"
    MIN_CLIENT_VERSION: str = "1.0.0"

    PORT: int = int(os.environ.get("PORT", "8000"))
    HOST: str = os.environ.get("HOST", "0.0.0.0")

    # CORS configuration
    _allowed_origins_raw = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:4173,https://agastya-fleet.netlify.app"
    )
    ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _allowed_origins_raw.split(",") if origin.strip()]

    # Optimization job limits
    MAX_JOB_SECONDS: int = int(os.environ.get("MAX_JOB_SECONDS", "180"))
    MAX_FLEET_SIZE: int = int(os.environ.get("MAX_FLEET_SIZE", "100"))
    MAX_CONCURRENT_JOBS: int = int(os.environ.get("MAX_CONCURRENT_JOBS", "3"))
    MAX_STORED_JOBS: int = int(os.environ.get("MAX_STORED_JOBS", "100"))

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120"))

    # Request size limits (2MB maximum payload)
    MAX_PAYLOAD_BYTES: int = 2 * 1024 * 1024

    # Seed
    DEFAULT_SEED: int = int(os.environ.get("DEFAULT_SEED", "42"))


settings = Settings()
