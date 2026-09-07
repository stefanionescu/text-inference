"""Worker distribution and task management for benchmark runs.

This module provides utilities for distributing benchmark requests across
concurrent workers and managing the async task lifecycle.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from .connection import execute_connection
from tests.harness.client.concurrency import distribute_requests

if TYPE_CHECKING:
    from tests.state import BenchmarkConfig


async def run_worker(count: int, config: BenchmarkConfig) -> list[dict[str, Any]]:
    """Execute multiple sequential connections for a single worker.

    Args:
        count: Number of connections this worker should make.
        config: Benchmark configuration.

    Returns:
        Flattened list of results from all connections.

    """
    results: list[dict[str, Any]] = []
    for _ in range(count):
        results.extend(await execute_connection(config))
    return results


async def run_benchmark_workers(
    total_requests: int,
    concurrency: int,
    config: BenchmarkConfig,
) -> list[dict[str, Any]]:
    """Run concurrent workers until all benchmark requests complete.

    Distributes requests across workers and launches them all at once.

    Args:
        total_requests: Total number of benchmark requests.
        concurrency: Number of concurrent workers.
        config: Benchmark configuration.

    Returns:
        Flattened list of all results.

    """
    counts = distribute_requests(total_requests, concurrency)
    tasks = [asyncio.create_task(run_worker(count, config)) for count in counts if count > 0]
    nested = await asyncio.gather(*tasks)
    return [item for sublist in nested for item in sublist]


__all__ = [
    "run_benchmark_workers",
    "run_worker",
]
