"""Sampling configuration data shapes."""

from __future__ import annotations

from dataclasses import dataclass

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


__all__ = [
    "DynamicSamplingField",
    "NumericSamplingValue",
    "SamplingCaster",
    "SamplingFieldSpec",
]
