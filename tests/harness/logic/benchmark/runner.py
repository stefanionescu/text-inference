"""Benchmark runner for WebSocket /ws endpoint performance testing.

This module orchestrates bounded concurrent runs and reports response latency.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from .reporting import print_report
from tests.state import BenchmarkConfig
from .workers import run_benchmark_workers
from tests.harness.client.prompt import select_prompt
from tests.harness.client.selection import choose_message
from config.tests.defaults import BENCHMARK_FALLBACK_MESSAGE
from tests.harness.client.concurrency import sanitize_concurrency

if TYPE_CHECKING:
    import argparse


def _build_config(arguments: argparse.Namespace) -> BenchmarkConfig:
    """Build benchmark configuration from CLI arguments."""
    message = choose_message(arguments.message, fallback=BENCHMARK_FALLBACK_MESSAGE)
    sampling = getattr(arguments, "sampling", None) or None
    is_double_ttfb_enabled = bool(arguments.is_double_ttfb_enabled)
    prompt = select_prompt(arguments.gender, arguments.personality)

    return BenchmarkConfig(
        server_url=arguments.server,
        api_key=arguments.api_key,
        gender=arguments.gender,
        personality=arguments.personality,
        prompt=prompt,
        message=message,
        timeout_seconds=float(arguments.timeout),
        sampling=sampling,
        is_double_ttfb_enabled=is_double_ttfb_enabled,
    )


async def run_benchmark(arguments: argparse.Namespace) -> bool:
    """Parse benchmark arguments and execute the benchmark.

    Returns:
        True if all requests succeeded, False if any failed.

    """
    config = _build_config(arguments)
    requests, concurrency = sanitize_concurrency(
        int(arguments.requests),
        int(arguments.concurrency),
    )

    results = await run_benchmark_workers(requests, concurrency, config)

    print_report(
        config.server_url,
        requests,
        concurrency,
        results,
        is_double_ttfb_enabled=config.is_double_ttfb_enabled,
    )
    return all(result.get("ok") for result in results)


__all__ = ["run_benchmark"]
