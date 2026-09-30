"""
Unit tests for asynchronous job store, concurrency caps, rate limiting, and cancellations.
"""

import time
import pytest
from app.jobs.job_store import job_store, JobRecord
from app.core.config import settings
from app.core.errors import JobNotFoundError, JobQueueFullError, RateLimitExceededError


def test_job_lifecycle():
    spec = {"generations": 20}
    job = job_store.create_job(algorithm="QIEA", problem_spec=spec)
    assert job.status == "QUEUED"
    assert job.progress_percent == 0.0

    retrieved = job_store.get_job(job.job_id)
    assert retrieved.job_id == job.job_id

    cancelled = job_store.cancel_job(job.job_id)
    assert cancelled.status == "CANCELLED"
    assert cancelled.cancellation_requested is True


def test_job_not_found():
    with pytest.raises(JobNotFoundError):
        job_store.get_job("job_non_existent_123")


def test_concurrency_cap():
    orig_cap = settings.MAX_CONCURRENT_JOBS
    settings.MAX_CONCURRENT_JOBS = 2
    try:
        j1 = job_store.create_job("QIEA", {})
        j1.status = "RUNNING"
        j2 = job_store.create_job("QIEA", {})
        j2.status = "RUNNING"

        # Third job should exceed concurrency cap
        with pytest.raises(JobQueueFullError):
            job_store.create_job("QIEA", {})
    finally:
        settings.MAX_CONCURRENT_JOBS = orig_cap


def test_rate_limiting():
    ip = "192.168.1.100"
    orig_limit = settings.RATE_LIMIT_PER_MINUTE
    settings.RATE_LIMIT_PER_MINUTE = 5
    try:
        for _ in range(5):
            job_store.check_rate_limit(ip)

        # 6th request within minute raises RateLimitExceededError
        with pytest.raises(RateLimitExceededError):
            job_store.check_rate_limit(ip)
    finally:
        settings.RATE_LIMIT_PER_MINUTE = orig_limit


def test_bounded_job_store_eviction():
    orig_max = settings.MAX_STORED_JOBS
    settings.MAX_STORED_JOBS = 3
    try:
        j1 = job_store.create_job("QIEA", {})
        j1.status = "COMPLETED"
        j2 = job_store.create_job("QIEA", {})
        j2.status = "COMPLETED"
        j3 = job_store.create_job("QIEA", {})
        j3.status = "COMPLETED"

        # 4th job should evict j1
        j4 = job_store.create_job("QIEA", {})

        with pytest.raises(JobNotFoundError):
            job_store.get_job(j1.job_id)
        assert job_store.get_job(j4.job_id) is not None
    finally:
        settings.MAX_STORED_JOBS = orig_max
