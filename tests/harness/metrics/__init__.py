"""Metrics, timing, and result utilities.

This subpackage provides payload structures and utilities for tracking
benchmark metrics, TTFB samples, and result formatting.
"""

from .results import error_result, result_to_dict, success_result
from .durations import round_milliseconds, seconds_to_milliseconds
from .ttfb import emit_ttfb_summary, has_ttfb_samples, record_ttfb

__all__ = [
    # ttfb
    "emit_ttfb_summary",
    # results
    "error_result",
    "has_ttfb_samples",
    "record_ttfb",
    "result_to_dict",
    # durations
    "round_milliseconds",
    "seconds_to_milliseconds",
    "success_result",
]
