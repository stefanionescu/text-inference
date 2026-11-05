"""Model-card provenance fields and template formatting."""

from __future__ import annotations

import json
from string import Template
from typing import TYPE_CHECKING, cast
from pathlib import Path

from src.hf.license import read_license
from config.model.publishing import EMPTY_METADATA_ITEMS, HUGGING_FACE_MODEL_URL, MODEL_CARD_TEMPLATE_DIR
from config.model.quantization import HUB_SOURCE_KIND

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def read_metadata_section(metadata: Mapping[str, object], field_name: str) -> dict[str, object]:
    """Read one required metadata mapping."""
    value = metadata.get(field_name)
    if not isinstance(value, dict):
        message = f"Quantization metadata field {field_name} must be an object"
        raise TypeError(message)
    return cast("dict[str, object]", value)


def read_metadata_text(metadata: Mapping[str, object], field_name: str) -> str:
    """Read one required non-empty metadata string."""
    value = metadata.get(field_name)
    if not isinstance(value, str) or not value:
        message = f"Quantization metadata field {field_name} must be a string"
        raise TypeError(message)
    return value


def format_metadata_items(items: object) -> str:
    """Format a metadata sequence for human-readable cards."""
    if isinstance(items, list | tuple):
        metadata_items: Sequence[object] = cast("Sequence[object]", items)
        formatted_items = ", ".join(str(item) for item in metadata_items)
        return formatted_items or EMPTY_METADATA_ITEMS
    return str(items)


def build_provenance_fields(
    metadata: Mapping[str, object],
    repo_id: str,
    *,
    hf_token: str | None,
) -> dict[str, object]:
    """Build source, license, and provenance fields shared by both cards."""
    source = read_metadata_section(metadata, "source")
    source_model = read_metadata_text(source, "model")
    source_kind = read_metadata_text(source, "kind")
    source_revision = read_metadata_text(source, "resolved_revision")
    source_url = (
        HUGGING_FACE_MODEL_URL.format(model_name=source_model, source_revision=source_revision)
        if source_kind == HUB_SOURCE_KIND
        else ""
    )
    source_link = f"[{source_model}]({source_url})" if source_url else f"`{source_model}`"
    license_metadata = read_license(
        source_model,
        source_kind,
        source_revision,
        hf_token=hf_token,
    )
    return {
        "model_name": repo_id.rsplit("/", maxsplit=1)[-1],
        "base_model_yaml": json.dumps(source_model),
        "source_model_link": source_link,
        "source_revision": source_revision,
        "license_id_yaml": json.dumps(license_metadata.identifier),
        "license_name_yaml": json.dumps(license_metadata.name),
        "license_link_yaml": json.dumps(license_metadata.link),
        "license_name": license_metadata.name,
        "license_link": license_metadata.link,
        "generated_at": read_metadata_text(metadata, "created_at"),
    }


def format_model_card(template_name: str, card_fields: Mapping[str, object]) -> str:
    """Format one checked-in model-card template."""
    template_path = Path(__file__).with_name(MODEL_CARD_TEMPLATE_DIR) / template_name
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.substitute(card_fields)


__all__ = [
    "build_provenance_fields",
    "format_metadata_items",
    "format_model_card",
    "read_metadata_section",
    "read_metadata_text",
]
