"""
Seed management for reproducibility.
"""
import random
import os


def set_seed(seed: int) -> None:
    """
    Set random seed for reproducibility.

    Args:
        seed: Random seed value
    """
    random.seed(seed)
    # Note: We don't set numpy or torch seeds since we're not using them
    # If they're added later, include them here
    os.environ['PYTHONHASHSEED'] = str(seed)
