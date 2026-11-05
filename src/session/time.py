"""Time classification and formatting utilities.

This module provides utilities for working with timestamps in session metadata.
It generates structured timestamp information that includes:

- ISO 8601 formatted time
- Human-readable classification (Morning, Afternoon, Evening, etc.)
- Display string combining ISO and classification
- Timezone name

The classification allows prompts to reference time of day naturally,
e.g., "Good morning" vs "Good evening" in system prompts.
"""

from __future__ import annotations

from datetime import UTC, tzinfo, datetime
from dataclasses import dataclass

from config.runtime.session_time import TIME_CLASSIFICATIONS


@dataclass(frozen=True, slots=True)
class SessionTimestamp:
    """Structured representation of a session timestamp.

    Attributes:
        iso_timestamp: Time of the iso.
        classification: Class of the error.
        display: Text to show for the value.
        timezone_name: Name of the timezone.

    """

    iso_timestamp: str
    classification: str
    display: str
    timezone_name: str


def classify_hour(hour: int) -> str:
    """Classify time of day based on hour.

    Args:
        hour: Hour in 24-hour format (0-23)

    Returns:
        Time classification string

    """
    for start, end, classification in TIME_CLASSIFICATIONS:
        if start <= hour <= end:
            return classification
    return "Unknown"


def format_session_timestamp(
    *,
    current_time: datetime | None = None,
    timezone: tzinfo | None = None,
) -> SessionTimestamp:
    """Generate a timezone-aware timestamp for session metadata.

    Args:
        current_time: Optional datetime to format. Defaults to current UTC time.
        timezone: Target timezone. Defaults to UTC.

    Returns:
        SessionTimestamp: Structured timestamp with ISO, classification, and human display value.

    """
    target_timezone = timezone or UTC
    current = current_time or datetime.now(tz=UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    localized = current.astimezone(target_timezone)

    classification = classify_hour(localized.hour)
    iso_timestamp = localized.replace(microsecond=0).isoformat()

    return SessionTimestamp(
        iso_timestamp=iso_timestamp,
        classification=classification,
        display=f"{iso_timestamp} ({classification})",
        timezone_name=localized.tzname() or str(target_timezone),
    )


__all__ = ["SessionTimestamp", "classify_hour", "format_session_timestamp"]
