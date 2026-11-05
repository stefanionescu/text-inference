"""Warmup script helpers.

Provides Python utilities used by warmup profile selection.
"""

from __future__ import annotations

import sys

from config.prompt.profiles import WARMUP_PROMPT_PAIRS


def list_prompt_pairs() -> list[tuple[str, str]]:
    """Return shared gender and personality pairs for warmup selection.

    Returns:
        List of (gender, personality) tuples.

    """
    prompt_pairs: list[tuple[str, str]] = []
    for gender, personality in WARMUP_PROMPT_PAIRS:
        if not gender:
            continue
        prompt_pairs.append((gender, personality or ""))
    return prompt_pairs


def print_prompt_pairs() -> None:
    """Print prompt pairs in gender:personality format for shell consumption."""
    prompt_pairs = list_prompt_pairs()
    for gender, personality in prompt_pairs:
        sys.stdout.write(str(f"{gender}:{personality}") + "\n")


if __name__ == "__main__":
    print_prompt_pairs()
