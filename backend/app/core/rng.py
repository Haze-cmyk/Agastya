"""
Agastya Seeded Random Number Generator Manager
Guarantees deterministic, reproducible results across metaheuristics and baseline regressions.
"""

from __future__ import annotations
import random
from typing import Optional
import numpy as np


def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """Returns a seeded NumPy Generator instance."""
    if seed is None:
        seed = 42
    return np.random.default_rng(seed)


def seed_all(seed: Optional[int] = None) -> int:
    """Sets standard library random and numpy seed globally if needed."""
    effective_seed = seed if seed is not None else 42
    random.seed(effective_seed)
    np.random.seed(effective_seed)
    return effective_seed
