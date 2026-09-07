"""Session timestamp classification policy."""

from __future__ import annotations

HOUR_MIDNIGHT = 0
NIGHT_START = 1
NIGHT_END = 3
EARLY_MORNING_START = 4
EARLY_MORNING_END = 6
MORNING_START = 7
MORNING_END = 11
HOUR_NOON = 12
AFTERNOON_START = 13
AFTERNOON_END = 16
EARLY_EVENING_START = 17
EARLY_EVENING_END = 20
EVENING_START = 21
EVENING_END = 23

TIME_CLASSIFICATIONS = (
    (0, 0, "Midnight"),
    (1, 3, "Night"),
    (4, 6, "Early Morning"),
    (7, 11, "Morning"),
    (12, 12, "Noon"),
    (13, 16, "Afternoon"),
    (17, 20, "Early Evening"),
    (21, 23, "Evening"),
)

__all__ = [
    "AFTERNOON_END",
    "AFTERNOON_START",
    "EARLY_EVENING_END",
    "EARLY_EVENING_START",
    "EARLY_MORNING_END",
    "EARLY_MORNING_START",
    "EVENING_END",
    "EVENING_START",
    "HOUR_MIDNIGHT",
    "HOUR_NOON",
    "MORNING_END",
    "MORNING_START",
    "NIGHT_END",
    "NIGHT_START",
    "TIME_CLASSIFICATIONS",
]
