"""Benchmark reporting with clean, consistent formatting.

Provides summary output for benchmark runs including latency percentiles,
error breakdown, and phase-separated metrics for double-ttfb mode.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from tests.harness.reporting.terminal import dim, red, bold, green, write_line, section_header

if TYPE_CHECKING:
    from collections.abc import Iterable

PHASE_FIRST = 1
PHASE_SECOND = 2

# ============================================================================
# Internal Helpers
# ============================================================================


def percentile(values: list[float], fraction: float, *, is_previous_selected: bool = False) -> float:
    """Return the selected percentile from a list of samples."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    sample_count = len(sorted_values)
    index = int(fraction * sample_count)
    if is_previous_selected:
        index = max(index - 1, 0)
    index = min(index, sample_count - 1)
    return sorted_values[index]


def _is_capacity_error(message: str | None) -> bool:
    if not message:
        return False
    message = message.lower()
    return "server_at_capacity" in message or "1013" in message


def _format_error_hint(raw_error: str, all_errors: list[dict[str, Any]]) -> str:
    message = raw_error or "unknown error"
    normalized = message.lower()
    failure_hint = message

    if "authentication_failed" in normalized:
        api_key = os.getenv("API_KEY")
        if api_key:
            failure_hint = "authentication_failed - provided API_KEY was rejected"
        else:
            failure_hint = "authentication_failed - API_KEY environment variable is missing"
    elif "server_at_capacity" in normalized:
        capacity_errors = [error for error in all_errors if _is_capacity_error(error.get("error"))]
        context_fields: list[str] = []
        if capacity_errors:
            context_fields.append(f"rejections={len(capacity_errors)}")
        connection_limit = os.getenv("MAX_CONCURRENT_CONNECTIONS")
        if connection_limit:
            context_fields.append(f"MAX_CONCURRENT_CONNECTIONS={connection_limit}")
        context_suffix = f" ({', '.join(context_fields)})" if context_fields else ""
        failure_hint = f"server_at_capacity{context_suffix}"
    elif "connection_closed_ok" in normalized:
        closed_count = sum(1 for error in all_errors if "connection_closed" in str(error.get("error", "")).lower())
        failure_hint = f"connection closed (code 1000) before completion ({closed_count} affected)"
    elif "connection_closed" in normalized:
        failure_hint = f"connection closed unexpectedly: {message}"

    return failure_hint


def _format_latency_line(label: str, samples: list[float]) -> str:
    """Format a latency statistics line."""
    if not samples:
        return ""
    p50 = percentile(samples, 0.5)
    p95 = percentile(samples, 0.95, is_previous_selected=True)
    average = sum(samples) / len(samples)
    return f"  {label:>12}  avg={average:>6.0f}ms  p50={p50:>6.0f}ms  p95={p95:>6.0f}ms  {dim(f'(n={len(samples)})')}"


def _print_latency_section(successful_results: Iterable[dict[str, Any]], prefix: str = "") -> None:
    results = list(successful_results)
    ttfb = [result["ttfb_ms"] for result in results if result.get("ttfb_ms") is not None]
    first_sentence = [result["first_sentence_ms"] for result in results if result.get("first_sentence_ms") is not None]
    first_three_words = [result["first_3_words_ms"] for result in results if result.get("first_3_words_ms") is not None]

    latency_series = [
        ("TTFB", ttfb),
        ("3-words", first_three_words),
        ("sentence", first_sentence),
    ]

    for label, samples in latency_series:
        line = _format_latency_line(label, samples)
        if line:
            write_line(f"{prefix}{line}")


def _print_tagged_section(tag: str, results: list[dict[str, Any]]) -> None:
    successful_results = [result for result in results if result.get("ok")]
    if not successful_results:
        return
    write_line(f"\n  {bold(tag.upper())} transaction:")
    _print_latency_section(successful_results)


# ============================================================================
# Public API
# ============================================================================


def print_report(
    server_url: str,
    requests: int,
    concurrency: int,
    results: list[dict[str, Any]],
    *,
    is_double_ttfb_enabled: bool = False,
) -> None:
    """Print benchmark summary report with consistent formatting."""
    successful_results = [result for result in results if result.get("ok")]
    errors = [result for result in results if not result.get("ok")]
    total_transactions = len(results)

    write_line(f"\n{section_header('BENCHMARK RESULTS')}")

    # Summary line
    successful_count_text = green(str(len(successful_results))) if successful_results else str(len(successful_results))
    error_count_text = red(str(len(errors))) if errors else str(len(errors))

    if not is_double_ttfb_enabled:
        write_line(dim(f"  url: {server_url}"))
        write_line(dim(f"  requests: {requests}  concurrency: {concurrency}"))
        write_line(f"  results: {successful_count_text} ok, {error_count_text} errors\n")
        _print_latency_section(successful_results)
    else:
        write_line(dim(f"  url: {server_url}"))
        write_line(dim(f"  connections: {requests}  transactions: {total_transactions}  concurrency: {concurrency}"))
        write_line(f"  results: {successful_count_text} ok, {error_count_text} errors")
        _print_tagged_section("first", [result for result in results if result.get("phase") == PHASE_FIRST])
        _print_tagged_section("second", [result for result in results if result.get("phase") == PHASE_SECOND])

    if errors:
        write_line()
        error_message = str(errors[0].get("error", "unknown error"))
        write_line(f"  {red('ERROR')}: {_format_error_hint(error_message, errors)}")


__all__ = ["percentile", "print_report"]
