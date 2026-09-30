"""
Agastya Bounded Thread-Safe Job Store and In-Memory Rate Limiter
Enforces job limits, LRU garbage collection, concurrency caps, and IP rate limiting.
"""

from __future__ import annotations
import time
import uuid
import threading
from collections import OrderedDict
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.core.errors import JobNotFoundError, JobQueueFullError, RateLimitExceededError


class JobRecord:
    def __init__(self, job_id: str, algorithm: str, problem_spec: Dict[str, Any]):
        self.job_id = job_id
        self.algorithm = algorithm
        self.problem_spec = problem_spec
        self.status = "QUEUED"
        self.progress_percent = 0.0
        self.current_generation = 0
        self.total_generations = problem_spec.get("generations", 50)
        self.pareto_front: List[Dict[str, Any]] = []
        self.hypervolume = 0.0
        self.spread_metric = 0.0
        self.error_message: Optional[str] = None
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.cancellation_requested = False

    def to_dict(self) -> Dict[str, Any]:
        elapsed = 0.0
        if self.started_at is not None:
            end = self.completed_at if self.completed_at is not None else time.time()
            elapsed = round(end - self.started_at, 2)

        return {
            "job_id": self.job_id,
            "algorithm": self.algorithm,
            "status": self.status,
            "progress_percent": round(self.progress_percent, 1),
            "current_generation": self.current_generation,
            "total_generations": self.total_generations,
            "elapsed_seconds": elapsed,
            "pareto_front": self.pareto_front,
            "hypervolume": self.hypervolume,
            "spread_metric": self.spread_metric,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


class JobStore:
    _instance: Optional[JobStore] = None
    _lock = threading.Lock()

    def __init__(self):
        self._jobs: OrderedDict[str, JobRecord] = OrderedDict()
        self._rate_limits: Dict[str, List[float]] = {}
        self._rate_limit_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> JobStore:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = JobStore()
        return cls._instance

    def check_rate_limit(self, client_ip: str) -> None:
        """Rate limits requests per client IP to RATE_LIMIT_PER_MINUTE."""
        now = time.time()
        window_seconds = 60.0
        limit = settings.RATE_LIMIT_PER_MINUTE

        with self._rate_limit_lock:
            timestamps = self._rate_limits.get(client_ip, [])
            # Filter timestamps within last minute
            valid_timestamps = [t for t in timestamps if now - t < window_seconds]
            if len(valid_timestamps) >= limit:
                raise RateLimitExceededError(
                    f"Rate limit of {limit} requests per minute exceeded. Please retry in a few seconds."
                )
            valid_timestamps.append(now)
            self._rate_limits[client_ip] = valid_timestamps

    def create_job(self, algorithm: str, problem_spec: Dict[str, Any]) -> JobRecord:
        with self._lock:
            # Check concurrent running/queued jobs
            active_count = sum(1 for j in self._jobs.values() if j.status in ("QUEUED", "RUNNING"))
            if active_count >= settings.MAX_CONCURRENT_JOBS:
                raise JobQueueFullError(
                    f"Job queue full ({active_count}/{settings.MAX_CONCURRENT_JOBS} active). Please retry when prior runs finish."
                )

            # Evict oldest completed/failed jobs if limit reached
            if len(self._jobs) >= settings.MAX_STORED_JOBS:
                for j_id, job in list(self._jobs.items()):
                    if job.status in ("COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"):
                        del self._jobs[j_id]
                        break

            job_id = f"job_{uuid.uuid4().hex[:10]}"
            record = JobRecord(job_id, algorithm, problem_spec)
            self._jobs[job_id] = record
            return record

    def get_job(self, job_id: str) -> JobRecord:
        with self._lock:
            if job_id not in self._jobs:
                raise JobNotFoundError(job_id)
            return self._jobs[job_id]

    def cancel_job(self, job_id: str) -> JobRecord:
        with self._lock:
            if job_id not in self._jobs:
                raise JobNotFoundError(job_id)
            job = self._jobs[job_id]
            job.cancellation_requested = True
            if job.status == "QUEUED":
                job.status = "CANCELLED"
                job.completed_at = time.time()
            return job


job_store = JobStore.get_instance()
