"""Terminal reporting for test clients.

This module provides consistent formatting helpers for displaying test
results in a readable, scannable format across all test scripts.
"""

from __future__ import annotations

import sys
from typing import Any
from functools import partial

# ANSI color codes (disabled if not a tty)
_USE_COLOR = sys.stdout.isatty()


def write_line(value: object = "") -> None:
    """Write one value followed by a newline."""
    text = f"{value}\n"
    written = sys.stdout.write(text)
    if written < len(text):
        sys.stdout.flush()


def write_text(value: object = "", *, is_flush_requested: bool = False) -> None:
    """Write one value without appending a newline."""
    text = str(value)
    sys.stdout.write(text)
    if is_flush_requested:
        sys.stdout.flush()


def _format_ansi_text(code: str, text: str) -> str:
    """Wrap text in ANSI color codes if output is a tty."""
    formatted = f"\033[{code}m{text}\033[0m"
    if not _USE_COLOR:
        return text
    return formatted


dim = partial(_format_ansi_text, "2")
bold = partial(_format_ansi_text, "1")
green = partial(_format_ansi_text, "32")
red = partial(_format_ansi_text, "31")
cyan = partial(_format_ansi_text, "36")
yellow = partial(_format_ansi_text, "33")
magenta = partial(_format_ansi_text, "35")


# ============================================================================
# Visual separators
# ============================================================================


def section_header(title: str, width: int = 60) -> str:
    """Create a prominent section header."""
    padding = width - len(title) - 4
    left = padding // 2
    right = padding - left
    return bold(f"{'─' * left}[ {title} ]{'─' * right}")


def case_header(name: str) -> str:
    """Create a test case header."""
    header = section_header(name)
    prefix = "\n"
    return f"{prefix}{header}"


def exchange_header(index: int | None = None, profile: str | None = None, gender: str | None = None) -> str:
    """Create an exchange header with optional profile metadata."""
    label_fields: list[str] = []
    if index is not None:
        label_fields.append(f"#{index:02d}")
    if profile and gender:
        label_fields.append(f"{profile}/{gender}")
    elif profile:
        label_fields.append(profile)
    elif gender:
        label_fields.append(gender)

    label = " ".join(label_fields) if label_fields else "Exchange"
    return dim(f"┌─ {label} {'─' * (50 - len(label))}")


def exchange_footer() -> str:
    """Create an exchange footer."""
    width = 55
    border = "└" + "─" * width
    return dim(border)


# ============================================================================
# Message formatting
# ============================================================================


def format_user(text: str) -> str:
    """Format a user message."""
    label = cyan("USER")
    prefix = f"{label}  "
    return f"{prefix}{text}"


def format_assistant(text: str) -> str:
    """Format an assistant message."""
    label = magenta("ASST")
    prefix = f"{label}  "
    return f"{prefix}{text}"


def format_metrics_inline(metrics: dict[str, Any]) -> str:
    """Format metrics as a compact inline string."""
    metric_fields: list[str] = []

    first_byte_latency_milliseconds = metrics.get("ttfb_ms")
    if first_byte_latency_milliseconds is not None:
        metric_fields.append(f"ttfb={first_byte_latency_milliseconds:.0f}ms")

    first_three_words_milliseconds = metrics.get("time_to_first_3_words_ms")
    if first_three_words_milliseconds is not None:
        metric_fields.append(f"3w={first_three_words_milliseconds:.0f}ms")

    first_sentence_milliseconds = metrics.get("time_to_first_complete_sentence_ms")
    if first_sentence_milliseconds is not None:
        metric_fields.append(f"sent={first_sentence_milliseconds:.0f}ms")

    total_milliseconds = metrics.get("total_ms")
    if total_milliseconds is not None:
        metric_fields.append(f"total={total_milliseconds:.0f}ms")

    chunk_count = metrics.get("chunks")
    character_count = metrics.get("chars")
    if chunk_count is not None and character_count is not None:
        metric_fields.append(f"{chunk_count}chunks/{character_count}chars")

    return dim(" · ".join(metric_fields)) if metric_fields else ""


# ============================================================================
# Test result formatting
# ============================================================================


def format_pass(label: str) -> str:
    """Format a passing test result."""
    status = green("✓ PASS")
    prefix = f"{status}  "
    return f"{prefix}{label}"


def format_fail(label: str, reason: str = "") -> str:
    """Format a failing test result."""
    suffix = f": {reason}" if reason else ""
    status = red("✗ FAIL")
    prefix = f"{status}  "
    return f"{prefix}{label}{suffix}"


def format_status(text: str) -> str:
    """Format informational text."""
    indent = "  "
    status_text = f"{indent}{text}"
    return dim(status_text)


# ============================================================================
# TTFB summary formatting
# ============================================================================


def format_ttfb_summary(
    kind: str,
    stats: dict[str, float | int],
    label: str = "TTFB",
) -> str:
    """Format TTFB summary statistics in a readable table row."""
    statistic_fields = [
        f"{bold(label)} {yellow(kind):>4}",
        f"first={stats['first']:>6.0f}ms",
        f"avg={stats['average']:>6.0f}ms",
        f"p50={stats['p50']:>6.0f}ms",
        f"p90={stats['p90']:>6.0f}ms",
        f"p95={stats['p95']:>6.0f}ms",
        dim(f"(n={stats['count']})"),
    ]
    separator = "  "
    return separator.join(statistic_fields)


# ============================================================================
# Connection test formatting
# ============================================================================


def connection_test_header(name: str) -> str:
    """Create a connection test section header."""
    title = bold(f"▶ {name.upper()}")
    suffix = " connection test"
    return f"\n{title}{suffix}"


def connection_status(label: str, message: str) -> str:
    """Format a connection status update."""
    indent = "  "
    status_text = f"{indent}[{label}] {message}"
    return dim(status_text)


def connection_pass(label: str) -> str:
    """Format a connection test pass."""
    icon = green("✓")
    status = green("PASS")
    return f"  {icon} [{label}] {status}"


def connection_fail(label: str, reason: str) -> str:
    """Format a connection test failure."""
    icon = red("✗")
    status = red("FAIL")
    return f"  {icon} [{label}] {status}: {reason}"


__all__ = [
    "bold",
    "case_header",
    "connection_fail",
    "connection_pass",
    "connection_status",
    "connection_test_header",
    "cyan",
    "dim",
    "exchange_footer",
    "exchange_header",
    "format_assistant",
    "format_fail",
    "format_metrics_inline",
    "format_pass",
    "format_status",
    "format_ttfb_summary",
    "format_user",
    "green",
    "magenta",
    "red",
    "section_header",
    "write_line",
    "write_text",
    "yellow",
]
