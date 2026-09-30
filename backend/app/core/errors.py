"""
Agastya Custom Error Hierarchies and HTTP Exception Mappings
"""

from __future__ import annotations
from typing import Optional, Any, Dict


class AgastyaError(Exception):
    """Base exception for Agastya application errors."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class AgastyaValidationError(AgastyaError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class JobNotFoundError(AgastyaError):
    def __init__(self, job_id: str):
        super().__init__(f"Optimization job '{job_id}' not found.", status_code=404, details={"job_id": job_id})


class RateLimitExceededError(AgastyaError):
    def __init__(self, message: str = "Rate limit exceeded. Please retry shortly."):
        super().__init__(message, status_code=429)


class JobQueueFullError(AgastyaError):
    def __init__(self, message: str = "Maximum concurrent optimization jobs reached. Please try again later."):
        super().__init__(message, status_code=429)


class PayloadTooLargeError(AgastyaError):
    def __init__(self, message: str = "Payload exceeds maximum allowed limit of 2MB."):
        super().__init__(message, status_code=413)


class InfeasibleOptimizationError(AgastyaError):
    def __init__(self, message: str, violations: Optional[list] = None):
        super().__init__(message, status_code=400, details={"violations": violations or []})
