"""Concurrency utilities for benchmark and test runners.

This module provides helpers for managing concurrent workloads,
including request distribution and parameter sanitization.
"""

from __future__ import annotations


def sanitize_concurrency(requests: int, concurrency: int) -> tuple[int, int]:
    """Ensure request and concurrency values are valid.

    Args:
        requests: Total number of requests.
        concurrency: Desired concurrency level.

    Returns:
        Tuple of (safe_requests, safe_concurrency) where both are >= 1
        and concurrency <= requests.

    """
    safe_requests = max(1, requests)
    safe_concurrency = max(1, min(concurrency, safe_requests))
    return safe_requests, safe_concurrency


def distribute_requests(total: int, concurrency: int) -> list[int]:
    """Distribute requests across workers as evenly as possible.

    Args:
        total: Total number of requests to distribute.
        concurrency: Number of workers.

    Returns:
        List of request counts per worker.

    """
    base, remainder = divmod(total, concurrency)
    return [base + (1 if i < remainder else 0) for i in range(concurrency)]


__all__ = ["distribute_requests", "sanitize_concurrency"]
