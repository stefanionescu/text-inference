"""Time-to-first-byte aggregation utilities.

This module provides functions for accumulating TTFB samples and computing
summary statistics (p50, p90, p95). Uses TTFBSamples from tests.state for payload.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any
from tests.harness.reporting.terminal import bold, dim, section_header

if TYPE_CHECKING:
    from tests.state.metrics import TTFBSamples
    from collections.abc import Callable, Mapping, Sequence

# ============================================================================
# Internal Helpers
# ============================================================================


def _percentile(samples: Sequence[float], fraction: float) -> float:
    """Compute the given percentile (0-1) from sorted samples."""
    if not samples:
        message = "percentile requires at least one sample"
        raise ValueError(message)
    if fraction <= 0:
        return min(samples)
    if fraction >= 1:
        return max(samples)
    sorted_samples = sorted(samples)
    position = fraction * (len(sorted_samples) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_samples[lower_index]
    weight = position - lower_index
    return sorted_samples[lower_index] + (sorted_samples[upper_index] - sorted_samples[lower_index]) * weight


def _parse_milliseconds(value: object) -> float | None:
    """Return a numeric millisecond value when present."""
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return float(str(value))


def _build_stats(samples: Sequence[float]) -> dict[str, float | int]:
    """Build a stats dict from a sequence of samples."""
    count = len(samples)
    first = samples[0] if samples else 0
    return {
        "count": count,
        "first": first,
        "average": sum(samples) / count if count else 0,
        "p50": _percentile(samples, 0.50) if samples else 0,
        "p90": _percentile(samples, 0.90) if samples else 0,
        "p95": _percentile(samples, 0.95) if samples else 0,
    }


def _format_milliseconds(value: float | None) -> str:
    """Format milliseconds value."""
    if value is None:
        return "—"
    formatted = f"{value:.0f}"
    return f"{formatted}ms"


def _format_stats_line(
    label: str,
    stats: dict[str, float | int],
    *,
    is_first_shown: bool = False,
) -> str:
    """Format a stats line for a metric."""
    fields = [f"  {bold(label):>10}"]

    if is_first_shown:
        fields.append(f"first={stats['first']:>6.0f}ms")

    fields.extend(
        [
            f"avg={stats['average']:>6.0f}ms",
            f"p50={stats['p50']:>6.0f}ms",
            f"p90={stats['p90']:>6.0f}ms",
            f"p95={stats['p95']:>6.0f}ms",
            dim(f"(n={stats['count']})"),
        ],
    )

    return "  ".join(fields)


def _emit_first_message(samples: TTFBSamples, sink: Callable[[str], None]) -> None:
    """Emit first message latency (includes prefill overhead)."""
    fields = [f"  {bold('FIRST')}  {dim('(includes prefill)')}"]

    if samples.samples:
        fields.append(f"ttfb={_format_milliseconds(samples.samples[0])}")
    if samples.first_three_words_samples:
        fields.append(f"3w={_format_milliseconds(samples.first_three_words_samples[0])}")
    if samples.first_sentence_samples:
        fields.append(f"sent={_format_milliseconds(samples.first_sentence_samples[0])}")

    sink("  ".join(fields))


def _emit_remaining_stats(samples: TTFBSamples, sink: Callable[[str], None]) -> None:
    """Emit statistics for messages after the first."""
    metrics = [
        ("TTFB", samples.samples[1:]),
        ("3-WORDS", samples.first_three_words_samples[1:] if len(samples.first_three_words_samples) > 1 else []),
        ("SENTENCE", samples.first_sentence_samples[1:] if len(samples.first_sentence_samples) > 1 else []),
    ]

    for label, sample_list in metrics:
        if not sample_list:
            continue
        stats = _build_stats(sample_list)
        sink(_format_stats_line(label, stats))


def _emit_single_stats(samples: TTFBSamples, sink: Callable[[str], None]) -> None:
    """Emit stats when we only have a single sample."""
    metrics = [
        ("TTFB", samples.samples),
        ("3-WORDS", samples.first_three_words_samples),
        ("SENTENCE", samples.first_sentence_samples),
    ]

    for label, sample_list in metrics:
        if not sample_list:
            continue
        stats = _build_stats(sample_list)
        sink(_format_stats_line(label, stats, is_first_shown=True))


# ============================================================================
# Public Functions
# ============================================================================


def record_ttfb(samples: TTFBSamples, metrics: Mapping[str, Any]) -> None:
    """Record latency values from a metrics dict."""
    first_byte_latency_milliseconds = _parse_milliseconds(metrics.get("ttfb_ms"))
    first_three_words_milliseconds = _parse_milliseconds(metrics.get("time_to_first_3_words_ms"))
    first_sentence_milliseconds = _parse_milliseconds(metrics.get("time_to_first_complete_sentence_ms"))

    if first_byte_latency_milliseconds is not None:
        samples.samples.append(first_byte_latency_milliseconds)
    if first_three_words_milliseconds is not None:
        samples.first_three_words_samples.append(first_three_words_milliseconds)
    if first_sentence_milliseconds is not None:
        samples.first_sentence_samples.append(first_sentence_milliseconds)


def has_ttfb_samples(samples: TTFBSamples) -> bool:
    """Return True if any samples have been recorded."""
    primary_samples = samples.samples or samples.first_three_words_samples
    if primary_samples:
        return True
    return bool(samples.first_sentence_samples)


def emit_ttfb_summary(samples: TTFBSamples, sink: Callable[[str], None]) -> None:
    """Emit summary statistics with first message separated."""
    sink(section_header("LATENCY SUMMARY"))

    has_multiple_samples = len(samples.samples) > 1

    if has_multiple_samples:
        _emit_first_message(samples, sink)
        sink("")
        _emit_remaining_stats(samples, sink)
    else:
        _emit_single_stats(samples, sink)


__all__ = [
    "emit_ttfb_summary",
    "has_ttfb_samples",
    "record_ttfb",
]
