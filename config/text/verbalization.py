"""Text verbalization constants."""

from __future__ import annotations

DIGIT_WORDS: dict[str, str] = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}

OH_MAX_H_COUNT = 1
OH_MAX_O_COUNT = 2

__all__ = ["DIGIT_WORDS", "OH_MAX_H_COUNT", "OH_MAX_O_COUNT"]
