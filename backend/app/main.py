"""
Agastya API Application Entry Point
FastAPI application, CORS configuration, payload size middleware,
comprehensive exception handlers, and routing.
"""

from __future__ import annotations
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.errors import (
    AgastyaError,
    AgastyaValidationError,
    JobNotFoundError,
    RateLimitExceededError,
    JobQueueFullError,
    PayloadTooLargeError
)

from app.api.health import router as health_router
from app.api.predict import router as predict_router
from app.api.optimize import router as optimize_router
from app.api.scenarios import router as scenarios_router
from app.api.benchmark import router as benchmark_router
from app.api.data_routes import router as data_router


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects incoming HTTP requests with Content-Length exceeding 2MB."""
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.MAX_PAYLOAD_BYTES:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Payload too large. Maximum allowed size is 2MB."}
                    )
            except ValueError:
                pass
        return await call_next(request)


app = FastAPI(
    title=settings.API_TITLE,
    description="Quantum-Inspired Green Fleet Deployment, Fuel Prediction, and Emissions Optimization",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Payload size guard
app.add_middleware(PayloadSizeLimitMiddleware)

# 2. CORS middleware
_is_wildcard = "*" in settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _is_wildcard else settings.ALLOWED_ORIGINS,
    allow_origin_regex=None if _is_wildcard else r"^https://.*\.netlify\.app$|^https://.*\.railway\.app$|^https://.*\.up\.railway\.app$|^http://localhost(:\d+)?$|^http://127\.0\.0\.1(:\d+)?$",
    allow_credentials=False if _is_wildcard else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
def root_endpoint():
    """Root discovery endpoint providing service health and interactive API documentation."""
    return {
        "name": settings.API_TITLE,
        "description": "Agastya — Quantum-Inspired Green Fleet Optimizer API",
        "version": settings.VERSION,
        "status": "healthy",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "version": "/api/version",
            "predict": "/api/predict",
            "optimize": "/api/optimize",
            "jobs": "/api/jobs/{job_id}",
            "scenarios": "/api/scenarios/compare",
            "benchmark": "/api/benchmark",
            "vessels": "/api/data/vessels",
            "fuels": "/api/data/fuels",
            "ports": "/api/data/ports",
            "case_studies": "/api/data/case-studies"
        }
    }


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Translates Pydantic validation errors into clean field-level messages."""
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        errors.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Unprocessable Entity",
            "message": "Validation failed on one or more request fields.",
            "field_errors": errors
        }
    )


@app.exception_handler(AgastyaValidationError)
async def agastya_validation_handler(request: Request, exc: AgastyaValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation Error", "detail": exc.message, "details": exc.details}
    )


@app.exception_handler(JobNotFoundError)
async def job_not_found_handler(request: Request, exc: JobNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "detail": exc.message}
    )


@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Too Many Requests", "detail": exc.message}
    )


@app.exception_handler(JobQueueFullError)
async def queue_full_handler(request: Request, exc: JobQueueFullError):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Queue Full", "detail": exc.message}
    )


@app.exception_handler(PayloadTooLargeError)
async def payload_large_handler(request: Request, exc: PayloadTooLargeError):
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={"error": "Payload Too Large", "detail": exc.message}
    )


@app.exception_handler(AgastyaError)
async def general_agastya_handler(request: Request, exc: AgastyaError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Application Error", "detail": exc.message, "details": exc.details}
    )


# Attach Routers
app.include_router(health_router)
app.include_router(predict_router)
app.include_router(optimize_router)
app.include_router(scenarios_router)
app.include_router(benchmark_router)
app.include_router(data_router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Agastya API v{settings.VERSION} initialized successfully.")
