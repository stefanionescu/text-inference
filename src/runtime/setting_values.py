"""Parse one setting from a mapping of environment values, refusing malformed text."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.runtime.config import (
        EnvironmentValues,
    )


def parse_nullable_setting(
    environment: EnvironmentValues,
    name: str,
    default: str | None,
) -> str | None:
    """Read a nullable stripped string setting from an environment mapping.

    Args:
        environment: Environment variables to read.
        name: Name to use for the lookup.
        default: Value to use when the setting is absent.

    Returns:
        A nullable stripped string setting from an environment mapping.

    """
    raw_value = environment.get(name)
    if raw_value is None:
        return default
    normalized = str(raw_value).strip()
    return normalized or None


def parse_integer_setting(environment: EnvironmentValues, name: str, default: int) -> int:
    """Read an integer setting from an environment mapping.

    Args:
        environment: Environment variables to read.
        name: Name to use for the lookup.
        default: Value to use when the setting is absent.

    Returns:
        An integer setting from an environment mapping.

    Raises:
        ValueError: `name` must be an integer, got `raw_value`.

    """
    raw_value = environment.get(name)
    if raw_value is None or str(raw_value).strip() == "":
        return default
    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError) as exception:
        message = f"{name} must be an integer, got {raw_value!r}"
        raise ValueError(message) from exception


def parse_float_setting(environment: EnvironmentValues, name: str, default: float) -> float:
    """Read a float setting from an environment mapping.

    Args:
        environment: Environment variables to read.
        name: Name to use for the lookup.
        default: Value to use when the setting is absent.

    Returns:
        A float setting from an environment mapping.

    Raises:
        ValueError: `name` must be a float, got `raw_value`.

    """
    raw_value = environment.get(name)
    if raw_value is None or str(raw_value).strip() == "":
        return default
    try:
        return float(str(raw_value).strip())
    except (TypeError, ValueError) as exception:
        message = f"{name} must be a float, got {raw_value!r}"
        raise ValueError(message) from exception


def parse_boolean_setting(environment: EnvironmentValues, name: str) -> bool:
    """Read an exact zero-or-one boolean setting.

    Args:
        environment: Environment variables to read.
        name: Name to use for the lookup.

    Returns:
        An exact zero-or-one boolean setting.

    Raises:
        ValueError: `name` must be 0 or 1, got `raw_value`.

    """
    raw_value = environment.get(name)
    if raw_value is None:
        return False
    if raw_value == "0":
        return False
    if raw_value == "1":
        return True
    message = f"{name} must be 0 or 1, got {raw_value!r}"
    raise ValueError(message)


__all__ = ["parse_boolean_setting", "parse_float_setting", "parse_integer_setting", "parse_nullable_setting"]
