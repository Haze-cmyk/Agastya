"""
Agastya Fleet Optimization API Controller
Manages background job creation, status polling, and execution cancellation.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request, status
from app.schemas.schemas import (
    FleetOptimizationRequest,
    OptimizationLaunchResponse,
    OptimizationJobStatusResponse
)
from app.jobs.job_store import job_store
from app.jobs.runner import dispatch_optimization_job
from app.core.errors import JobNotFoundError, JobQueueFullError, RateLimitExceededError

router = APIRouter(tags=["Fleet Optimization"])


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post(
    "/api/optimize",
    response_model=OptimizationLaunchResponse,
    status_code=status.HTTP_202_ACCEPTED
)
def launch_fleet_optimization(request_body: FleetOptimizationRequest, request: Request):
    """
    Submits a multi-objective green fleet optimization job to the background queue.
    """
    client_ip = get_client_ip(request)

    # 1. Rate limiting check
    try:
        job_store.check_rate_limit(client_ip)
    except RateLimitExceededError as rle:
        raise HTTPException(status_code=429, detail=str(rle))

    # 2. Queue job
    problem_spec = request_body.model_dump()
    try:
        job = job_store.create_job(algorithm=request_body.algorithm, problem_spec=problem_spec)
    except JobQueueFullError as jqf:
        raise HTTPException(status_code=429, detail=str(jqf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue optimization job: {str(e)}")

    # 3. Dispatch worker
    dispatch_optimization_job(job.job_id)

    return OptimizationLaunchResponse(
        job_id=job.job_id,
        algorithm=job.algorithm,
        status=job.status,
        message="Optimization job successfully scheduled in background."
    )


@router.get("/api/jobs/{job_id}", response_model=OptimizationJobStatusResponse)
def get_job_status(job_id: str):
    """
    Polls execution status, progress percentage, and current Pareto front for a job.
    """
    try:
        job = job_store.get_job(job_id)
        return OptimizationJobStatusResponse(**job.to_dict())
    except JobNotFoundError as jne:
        raise HTTPException(status_code=404, detail=str(jne))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving job: {str(e)}")


@router.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """
    Signals cooperative cancellation of a queued or running optimization job.
    """
    try:
        job = job_store.cancel_job(job_id)
        return {
            "job_id": job.job_id,
            "status": job.status,
            "message": "Cancellation signal received."
        }
    except JobNotFoundError as jne:
        raise HTTPException(status_code=404, detail=str(jne))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling job: {str(e)}")
