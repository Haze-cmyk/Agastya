"""
Agastya Asynchronous Background Job Runner
Executes multi-objective fleet optimization routines in dedicated worker threads,
monitoring cancellation tokens and timeouts.
"""

from __future__ import annotations
import time
import threading
from typing import Dict, Any, List
import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.jobs.job_store import job_store, JobRecord
from app.optimizers.qiea import QIEAOptimizer
from app.optimizers.qi_pso import QIPSOOptimizer
from app.optimizers.nsga2 import NSGA2Optimizer
from app.optimizers.ga import ClassicalGAOptimizer
from app.optimizers.pso import ClassicalPSOOptimizer
from app.optimizers.pareto import compute_normalized_hypervolume, compute_spacing_metric


def run_optimization_job(job_id: str) -> None:
    job = job_store.get_job(job_id)
    job.status = "RUNNING"
    job.started_at = time.time()
    logger.info(f"Starting optimization job {job_id} using {job.algorithm}")

    algorithm_name = job.algorithm.upper()
    spec = job.problem_spec
    generations = spec.get("generations", 40)
    pop_size = spec.get("population_size", 30)
    seed = spec.get("seed", 42)

    # Instantiate chosen optimizer
    if algorithm_name == "QIEA":
        optimizer = QIEAOptimizer(spec, population_size=pop_size, generations=generations, seed=seed)
    elif algorithm_name in ("QI_PSO", "QIPSO", "QI-PSO"):
        optimizer = QIPSOOptimizer(spec, swarm_size=pop_size, iterations=generations, seed=seed)
    elif algorithm_name in ("NSGA2", "NSGA_2", "NSGA-II"):
        optimizer = NSGA2Optimizer(spec, population_size=pop_size, generations=generations, seed=seed)
    elif algorithm_name == "GA":
        optimizer = ClassicalGAOptimizer(spec, population_size=pop_size, generations=generations, seed=seed)
    elif algorithm_name == "PSO":
        optimizer = ClassicalPSOOptimizer(spec, swarm_size=pop_size, iterations=generations, seed=seed)
    else:
        # Default to QIEA
        optimizer = QIEAOptimizer(spec, population_size=pop_size, generations=generations, seed=seed)

    def progress_callback(current_gen: int, total_gen: int, current_front: List[Dict[str, Any]]) -> None:
        job.current_generation = current_gen
        job.total_generations = total_gen
        job.progress_percent = min(100.0, (current_gen / total_gen) * 100.0)

        # Copy non-dominated solutions to job
        clean_front = []
        for sol in current_front:
            item = dict(sol)
            item.pop("raw_bits", None)
            item.pop("raw_pos", None)
            item.pop("raw_genome", None)
            clean_front.append(item)

        job.pareto_front = clean_front

        # Compute metrics if front has solutions
        if clean_front:
            objs = np.array([
                [s["fuel_consumption_tonnes"], s["operating_cost_usd"], s["lifecycle_ghg_tco2e"]]
                for s in clean_front
            ], dtype=np.float64)
            job.hypervolume = compute_normalized_hypervolume(objs)
            job.spread_metric = round(compute_spacing_metric(objs), 2)

    def should_cancel() -> bool:
        if job.cancellation_requested:
            return True
        if job.started_at and (time.time() - job.started_at > settings.MAX_JOB_SECONDS):
            return True
        return False

    try:
        final_solutions = optimizer.optimize(
            progress_callback=progress_callback,
            should_cancel=should_cancel
        )

        job.completed_at = time.time()
        if job.cancellation_requested:
            job.status = "CANCELLED"
            logger.info(f"Job {job_id} cancelled by user.")
        elif job.started_at and (job.completed_at - job.started_at > settings.MAX_JOB_SECONDS):
            job.status = "TIMED_OUT"
            job.progress_percent = 100.0
            logger.warning(f"Job {job_id} reached maximum execution timeout of {settings.MAX_JOB_SECONDS}s.")
        else:
            job.status = "COMPLETED"
            job.progress_percent = 100.0
            logger.info(f"Job {job_id} completed successfully in {job.completed_at - job.started_at:.2f}s.")

    except Exception as e:
        logger.error(f"Error running optimization job {job_id}: {e}", exc_info=True)
        job.status = "FAILED"
        job.error_message = str(e)
        job.completed_at = time.time()


def dispatch_optimization_job(job_id: str) -> None:
    """Launches optimization in an asynchronous background thread."""
    thread = threading.Thread(target=run_optimization_job, args=(job_id,), daemon=True)
    thread.start()
