"""The sampling fields that a client may override, with their limits and error codes."""

from __future__ import annotations

from dataclasses import dataclass

NumericSamplingValue = float | int
SamplingCaster = type[float | int]


@dataclass(frozen=True)
class SamplingFieldSpec:
    """Validation metadata for a numeric sampling field.

    Attributes:
        name: Name to use for the lookup.
        caster: Function that converts the raw sampling value.
        minimum: Smallest accepted value.
        maximum: Largest accepted value.
        invalid_code: Code of the invalid.
        range_code: Code of the range.

    """

    name: str
    caster: SamplingCaster
    minimum: NumericSamplingValue
    maximum: NumericSamplingValue
    invalid_code: str
    range_code: str


@dataclass(frozen=True)
class DynamicSamplingField:
    """Sampling field metadata resolved from runtime settings.

    Attributes:
        name: Name to use for the lookup.
        caster: Function that converts the raw sampling value.
        minimum_attribute: Smallest allowed attribute.
        maximum_attribute: Largest allowed attribute.
        invalid_code: Code of the invalid.
        range_code: Code of the range.

    """

    name: str
    caster: SamplingCaster
    minimum_attribute: str
    maximum_attribute: str
    invalid_code: str
    range_code: str


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


__all__ = [
    "DYNAMIC_SAMPLING_FIELDS",
    "DynamicSamplingField",
    "NumericSamplingValue",
    "SamplingCaster",
    "SamplingFieldSpec",
]
