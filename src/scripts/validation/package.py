"""Package availability validation.

Checks whether a Python package is importable from shell scripts.

Usage:
    python -m src.scripts.validation.package importlinter   # exit 0 if installed
    python -m src.scripts.validation.package mypy           # exit 1 if missing
"""

from __future__ import annotations

import sys
import importlib.util

PACKAGE_MINIMUM_ARGUMENTS = 2


def main() -> int:
    """CLI entry point for shell script integration."""
    if len(sys.argv) < PACKAGE_MINIMUM_ARGUMENTS:
        return 1

    return 0 if importlib.util.find_spec(sys.argv[1]) is not None else 1


if __name__ == "__main__":
    sys.exit(main())
