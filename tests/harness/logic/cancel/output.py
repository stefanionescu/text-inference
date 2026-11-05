"""Result printing functions for cancel test output.

This module provides functions that format and print test results
to the console using the standard test output formatting helpers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.harness.reporting.terminal import (
    red,
    green,
    write_line,
    format_user,
    exchange_footer,
    exchange_header,
    format_assistant,
    format_metrics_inline,
)

if TYPE_CHECKING:
    from tests.state import (
        DrainPhaseResult,
        CancelPhaseResult,
        CancelClientResult,
        NormalClientResult,
        RecoveryPhaseResult,
    )

CANCEL_TEST_MESSAGE = "hey there! tell me a story about a magical forest"
RECOVERY_PREVIEW_CHARS = 80


def _print_cancel_phase(result: CancelPhaseResult) -> tuple[int, int]:
    if result.has_passed:
        write_line(f"  {green('✓')} [cancel] {green('PASS')}")
        return 1, 0
    reason = result.error or "cancelled=False"
    write_line(f"  {red('✗')} [cancel] {red('FAIL')}: {reason}")
    return 0, 1


def _print_drain_phase(result: DrainPhaseResult) -> tuple[int, int]:
    if result.has_passed:
        write_line(f"  {green('✓')} [drain] {green('PASS')}")
        return 1, 0
    reason = result.error or "spurious messages received"
    write_line(f"  {red('✗')} [drain] {red('FAIL')}: {reason}")
    return 0, 1


def _print_recovery_exchange(result: RecoveryPhaseResult) -> None:
    write_line(exchange_header())
    write_line(f"  {format_user(CANCEL_TEST_MESSAGE)}")
    response_preview = result.response_text[:RECOVERY_PREVIEW_CHARS]
    if len(result.response_text) > RECOVERY_PREVIEW_CHARS:
        response_preview += "..."
    write_line(f"  {format_assistant(response_preview)}")
    write_line(f"  {format_metrics_inline(result.metrics)}")
    write_line(exchange_footer())


def _print_recovery_phase(result: RecoveryPhaseResult) -> tuple[int, int]:
    if result.has_passed:
        _print_recovery_exchange(result)
        write_line(f"  {green('✓')} [recovery] {green('PASS')}")
        return 1, 0
    reason = result.error or "empty response"
    write_line(f"  {red('✗')} [recovery] {red('FAIL')}: {reason}")
    return 0, 1


def print_cancel_client_result(result: CancelClientResult) -> tuple[int, int]:
    """Print results for the canceling client.

    Args:
        result: Combined result from the canceling client.

    Returns:
        Tuple of (passed_count, failed_count).

    """
    cancel_passed, cancel_failed = _print_cancel_phase(result.cancel_phase)
    drain_passed, drain_failed = _print_drain_phase(result.drain_phase)
    recovery_passed, recovery_failed = _print_recovery_phase(result.recovery_phase)
    passed_count = cancel_passed + drain_passed + recovery_passed
    failed_count = cancel_failed + drain_failed + recovery_failed
    return passed_count, failed_count


def print_normal_client_results(results: list[NormalClientResult]) -> tuple[int, int]:
    """Print results for normal clients.

    Args:
        results: List of results from normal clients.

    Returns:
        Tuple of (passed_count, failed_count).

    """
    passed_count = 0
    failed_count = 0

    for result in results:
        label = f"client-{result.client_id}"
        if result.has_passed:
            write_line(f"  {green('✓')} [{label}] {green('PASS')}")
            passed_count += 1
        else:
            reason = result.error or "empty response"
            write_line(f"  {red('✗')} [{label}] {red('FAIL')}: {reason}")
            failed_count += 1

    return passed_count, failed_count


__all__ = [
    "CANCEL_TEST_MESSAGE",
    "print_cancel_client_result",
    "print_normal_client_results",
]
