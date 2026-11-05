"""Read source-model license metadata for generated model cards."""

from __future__ import annotations

from dataclasses import dataclass

from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

from config.model.publishing import (
    DEFAULT_LICENSE,
    LICENSE_ID_FIELD,
    LICENSE_LINK_FIELD,
    LICENSE_NAME_FIELD,
    LOCAL_LICENSE_PATH,
    HUGGING_FACE_MODEL_URL,
)
from config.model.quantization import HUB_SOURCE_KIND


@dataclass(frozen=True, slots=True)
class LicenseMetadata:
    """License fields rendered into one Hugging Face model card."""

    identifier: str
    name: str
    link: str


def _read_card_field(card_metadata: object, field_name: str) -> str | None:
    """Return one non-empty string from model-card metadata."""
    value = getattr(card_metadata, field_name, None)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _build_default_license(
    model_name: str,
    source_kind: str,
    source_revision: str,
) -> LicenseMetadata:
    """Return the selected `other` license fallback."""
    link = (
        HUGGING_FACE_MODEL_URL.format(model_name=model_name, source_revision=source_revision)
        if source_kind == HUB_SOURCE_KIND
        else LOCAL_LICENSE_PATH
    )
    return LicenseMetadata(identifier=DEFAULT_LICENSE, name=DEFAULT_LICENSE, link=link)


def read_license(
    model_name: str,
    source_kind: str,
    source_revision: str,
    *,
    hf_token: str | None,
) -> LicenseMetadata:
    """Read source license fields or return the selected `other` fallback."""
    default_license = _build_default_license(model_name, source_kind, source_revision)
    if source_kind != HUB_SOURCE_KIND:
        return default_license
    try:
        model_record = HfApi(token=hf_token).model_info(repo_id=model_name, revision=source_revision)
    except (HfHubHTTPError, OSError, ValueError):
        return default_license
    card_metadata = model_record.card_data
    license_id = _read_card_field(card_metadata, LICENSE_ID_FIELD)
    if license_id is None:
        return default_license
    return LicenseMetadata(
        identifier=license_id,
        name=_read_card_field(card_metadata, LICENSE_NAME_FIELD) or license_id,
        link=_read_card_field(card_metadata, LICENSE_LINK_FIELD)
        or HUGGING_FACE_MODEL_URL.format(model_name=model_name, source_revision=source_revision),
    )


__all__ = ["LicenseMetadata", "read_license"]
