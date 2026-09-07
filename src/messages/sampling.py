"""Sampling override validation and its field metadata."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from src.messages.validators import ValidationError


if TYPE_CHECKING:
    from collections.abc import Mapping
    from src.runtime.config import SamplingSettings

NumericSamplingValue = float | int
SamplingCaster = type[float | int]


@dataclass(frozen=True)
class SamplingFieldSpec:
    """Validation metadata for a numeric sampling field."""

    name: str
    caster: SamplingCaster
    minimum: NumericSamplingValue
    maximum: NumericSamplingValue
    invalid_code: str
    range_code: str


@dataclass(frozen=True)
class DynamicSamplingField:
    """Sampling field metadata resolved from runtime settings."""

    name: str
    caster: SamplingCaster
    minimum_attribute: str
    maximum_attribute: str
    invalid_code: str
    range_code: str


SamplingValue = float | int | bool

DYNAMIC_SAMPLING_FIELDS: tuple[DynamicSamplingField, ...] = (
    DynamicSamplingField(
        name="temperature",
        caster=float,
        minimum_attribute="minimum_temperature",
        maximum_attribute="maximum_temperature",
        invalid_code="invalid_temperature",
        range_code="temperature_out_of_range",
    ),
    DynamicSamplingField(
        name="top_p",
        caster=float,
        minimum_attribute="minimum_top_p",
        maximum_attribute="maximum_top_p",
        invalid_code="invalid_top_p",
        range_code="top_p_out_of_range",
    ),
    DynamicSamplingField(
        name="top_k",
        caster=int,
        minimum_attribute="minimum_top_k",
        maximum_attribute="maximum_top_k",
        invalid_code="invalid_top_k",
        range_code="top_k_out_of_range",
    ),
    DynamicSamplingField(
        name="min_p",
        caster=float,
        minimum_attribute="minimum_min_p",
        maximum_attribute="maximum_min_p",
        invalid_code="invalid_min_p",
        range_code="min_p_out_of_range",
    ),
    DynamicSamplingField(
        name="repetition_penalty",
        caster=float,
        minimum_attribute="minimum_repetition_penalty",
        maximum_attribute="maximum_repetition_penalty",
        invalid_code="invalid_repetition_penalty",
        range_code="repetition_penalty_out_of_range",
    ),
    DynamicSamplingField(
        name="presence_penalty",
        caster=float,
        minimum_attribute="minimum_presence_penalty",
        maximum_attribute="maximum_presence_penalty",
        invalid_code="invalid_presence_penalty",
        range_code="presence_penalty_out_of_range",
    ),
    DynamicSamplingField(
        name="frequency_penalty",
        caster=float,
        minimum_attribute="minimum_frequency_penalty",
        maximum_attribute="maximum_frequency_penalty",
        invalid_code="invalid_frequency_penalty",
        range_code="frequency_penalty_out_of_range",
    ),
)


def _parse_sampling_value(value: object, caster: SamplingCaster) -> NumericSamplingValue:
    """Coerce a raw value to the target sampling type."""
    if caster is int:
        return _parse_int(value)
    return _parse_float(value)


def _parse_float(value: object) -> float:
    """Coerce a value to float, rejecting bools and invalid types."""
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
    """Coerce a value to int, rejecting bools and non-integer floats."""
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


def _sampling_fields(
    sampling_settings: SamplingSettings,
) -> tuple[SamplingFieldSpec, ...]:
    """Return sampling field metadata from resolved settings."""
    return tuple(
        SamplingFieldSpec(
            name=field.name,
            caster=field.caster,
            minimum=getattr(sampling_settings, field.minimum_attribute),
            maximum=getattr(sampling_settings, field.maximum_attribute),
            invalid_code=field.invalid_code,
            range_code=field.range_code,
        )
        for field in DYNAMIC_SAMPLING_FIELDS
    )


def _get_sampling_block(message: Mapping[str, object]) -> Mapping[str, object]:
    """Return nested sampling overrides from a message."""
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
    """Read a sampling field from nested or top-level payload."""
    raw_value = sampling_block.get(field)
    if raw_value is None:
        raw_value = message.get(field)
    return raw_value


def _validate_numeric_field(
    raw_value: object,
    field: SamplingFieldSpec,
) -> NumericSamplingValue:
    """Validate and coerce one numeric sampling field."""
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
    """Extract numeric sampling overrides from a message."""
    overrides: dict[str, NumericSamplingValue] = {}
    for field in _sampling_fields(sampling_settings):
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
    """Extract the optional sanitize_output override."""
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

    Raises:
        ValidationError: If any parameter fails type or range validation.

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


__all__ = [
    "DynamicSamplingField",
    "NumericSamplingValue",
    "SamplingCaster",
    "SamplingFieldSpec",
    "extract_sampling_overrides",
]
