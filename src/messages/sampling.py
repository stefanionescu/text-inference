"""Sampling override validation and its field metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src.messages.validators import ValidationError

from .override_fields import DYNAMIC_SAMPLING_FIELDS, SamplingCaster, SamplingFieldSpec, NumericSamplingValue

if TYPE_CHECKING:
    from collections.abc import Mapping

    from src.runtime.config import SamplingSettings


SamplingValue = float | int | bool


def _parse_sampling_value(value: object, caster: SamplingCaster) -> NumericSamplingValue:
    """Coerce a raw value to the target sampling type.

    Args:
        value: Raw override value.
        caster: `int` selects integer parsing; any other caster selects float parsing.

    Returns:
        The parsed number.

    """
    if caster is int:
        return _parse_int(value)
    return _parse_float(value)


def _parse_float(value: object) -> float:
    """Coerce a value to float, rejecting bools and invalid types.

    Args:
        value: Raw override: a number or a numeric string.

    Returns:
        The value as a float.

    Raises:
        TypeError: The value is a bool or has an unsupported type.
        ValueError: The string is empty or does not parse as a float.

    """
    if isinstance(value, bool):
        message = "bool not allowed"
        raise TypeError(message)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            message = "empty string"
            raise ValueError(message)
        return float(stripped)
    message = "unsupported type"
    raise TypeError(message)


def _parse_int(value: object) -> int:
    """Coerce a value to int, rejecting bools and non-integer floats.

    Args:
        value: Raw override: an integer, a whole float, or a numeric string.

    Returns:
        The value as an int.

    Raises:
        TypeError: A bool or an unsupported type arrived instead of a number.
        ValueError: The float has a fraction, or the string is empty or does not parse as an integer.

    """
    if isinstance(value, bool):
        message = "bool not allowed"
        raise TypeError(message)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not value.is_integer():
            message = "non-integer float"
            raise ValueError(message)
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            message = "empty string"
            raise ValueError(message)
        return int(stripped)
    message = "unsupported type"
    raise TypeError(message)


def _get_sampling_block(message: Mapping[str, object]) -> Mapping[str, object]:
    """Return nested sampling overrides from a message.

    Args:
        message: Decoded client frame.

    Returns:
        The nested `sampling` mapping, or an empty mapping when the field is absent.

    Raises:
        ValidationError: The `sampling` field is present but is not an object.

    """
    sampling_block = message.get("sampling")
    if sampling_block is None:
        return {}
    if not isinstance(sampling_block, dict):
        error_code = "invalid_sampling_payload"
        raise ValidationError(error_code, "sampling must be an object")
    return cast("Mapping[str, object]", sampling_block)


def _read_field_value(
    field: str,
    message: Mapping[str, object],
    sampling_block: Mapping[str, object],
) -> object | None:
    """Read a sampling field from nested or top-level payload.

    Args:
        field: Override name to look up.
        message: Decoded client frame, read when the nested block has no value.
        sampling_block: Nested overrides, read first.

    Returns:
        The nested value, then the top-level value, or None when neither is set.

    """
    raw_value = sampling_block.get(field)
    if raw_value is None:
        raw_value = message.get(field)
    return raw_value


def _validate_numeric_field(
    raw_value: object,
    field: SamplingFieldSpec,
) -> NumericSamplingValue:
    """Validate and coerce one numeric sampling field.

    Args:
        raw_value: Override value as received.
        field: Spec with the caster, bounds, and error codes.

    Returns:
        The parsed number within the field bounds.

    Raises:
        ValidationError: The value does not parse, or it falls outside the field bounds.

    """
    try:
        normalized = _parse_sampling_value(raw_value, field.caster)
    except (TypeError, ValueError):
        raise ValidationError(field.invalid_code, f"{field.name} must be a valid {field.caster.__name__}") from None

    if not (field.minimum <= normalized <= field.maximum):
        raise ValidationError(
            field.range_code,
            f"{field.name} must be between {field.minimum} and {field.maximum}",
        )
    return normalized


def _extract_numeric_overrides(
    message: Mapping[str, object],
    sampling_block: Mapping[str, object],
    *,
    sampling_settings: SamplingSettings,
) -> dict[str, NumericSamplingValue]:
    """Extract numeric sampling overrides from a message.

    Args:
        message: Decoded client frame.
        sampling_block: Nested overrides from the frame.
        sampling_settings: Settings that supply each field's bounds.

    Returns:
        A validated value for each numeric field the client set.

    """
    overrides: dict[str, NumericSamplingValue] = {}
    resolved_fields = tuple(
        SamplingFieldSpec(
            name=dynamic_field.name,
            caster=dynamic_field.caster,
            minimum=getattr(sampling_settings, dynamic_field.minimum_attribute),
            maximum=getattr(sampling_settings, dynamic_field.maximum_attribute),
            invalid_code=dynamic_field.invalid_code,
            range_code=dynamic_field.range_code,
        )
        for dynamic_field in DYNAMIC_SAMPLING_FIELDS
    )
    for field in resolved_fields:
        raw_value = _read_field_value(field.name, message, sampling_block)
        if raw_value is None:
            continue
        overrides[field.name] = _validate_numeric_field(
            raw_value,
            field=field,
        )
    return overrides


def _extract_sanitize_override(
    message: Mapping[str, object],
    sampling_block: Mapping[str, object],
) -> bool | None:
    """Extract the optional sanitize_output override.

    Args:
        message: Frame that can carry a top-level `sanitize_output`.
        sampling_block: Nested overrides, read first.

    Returns:
        The client's bool, or None when the client did not set it.

    Raises:
        ValidationError: The client sent a value that is not a bool.

    """
    sanitize_raw = _read_field_value("sanitize_output", message, sampling_block)
    if sanitize_raw is None:
        return None
    if not isinstance(sanitize_raw, bool):
        error_code = "invalid_sanitize_output"
        raise ValidationError(error_code, "sanitize_output must be a boolean")
    return sanitize_raw


def extract_sampling_overrides(
    message: Mapping[str, object],
    *,
    sampling_settings: SamplingSettings,
) -> dict[str, SamplingValue]:
    """Extract and validate sampling parameter overrides from a message.

    Looks for parameters in both the top-level message and a nested
    ``sampling`` block.

    Args:
        message: The message mapping to extract parameters from.
        sampling_settings: Resolved sampling bounds.

    Returns:
        Dict of validated sampling overrides.

    """
    sampling_block = _get_sampling_block(message)
    overrides: dict[str, SamplingValue] = {
        **_extract_numeric_overrides(
            message,
            sampling_block,
            sampling_settings=sampling_settings,
        ),
    }
    sanitize_output = _extract_sanitize_override(message, sampling_block)
    if sanitize_output is not None:
        overrides["sanitize_output"] = sanitize_output

    return overrides


__all__ = ["extract_sampling_overrides"]
