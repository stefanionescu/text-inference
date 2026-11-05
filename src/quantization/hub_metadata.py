"""Read checkpoint metadata from the Hugging Face HTTP API with the standard library only."""

from __future__ import annotations

import re
from http import HTTPStatus
import json
from typing import cast
from http.client import HTTPSConnection
from urllib.parse import quote

from config.model.quantization import (
    HUB_COMMIT_PATTERN_TEXT,
    QUANTIZATION_CONFIG_FILENAMES,
)

_COMMIT_PATTERN = re.compile(HUB_COMMIT_PATTERN_TEXT)
_HUB_HOST = "huggingface.co"
_REQUEST_TIMEOUT_SECONDS = 30.0


def _mapping(value: object) -> dict[str, object]:
    """Return one string-keyed JSON mapping.

    Args:
        value: Value to check or convert.

    Returns:
        One string-keyed JSON mapping.

    Raises:
        TypeError: Hugging Face returned an invalid model response.

    """
    if not isinstance(value, dict):
        message = "Hugging Face returned an invalid model response"
        raise TypeError(message)
    return cast("dict[str, object]", value)


def _json_request(
    path: str,
    token: str | None,
    *,
    is_missing_allowed: bool = False,
) -> object | None:
    """Read one authenticated Hugging Face JSON response.

    Args:
        path: File system path.
        token: Hugging Face access token or token text.
        is_missing_allowed: Whether missing is allowed.

    Returns:
        One authenticated Hugging Face JSON response.

    Raises:
        RuntimeError: Hugging Face request failed with HTTP `status`: `path`.
        ValueError: Hugging Face request paths must be absolute.

    """
    if not path.startswith("/"):
        message = "Hugging Face request paths must be absolute"
        raise ValueError(message)
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    connection = HTTPSConnection(_HUB_HOST, timeout=_REQUEST_TIMEOUT_SECONDS)
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        if response.status == HTTPStatus.NOT_FOUND and is_missing_allowed:
            return None
        if not HTTPStatus.OK <= response.status < HTTPStatus.MULTIPLE_CHOICES:
            message = f"Hugging Face request failed with HTTP {response.status}: {path}"
            raise RuntimeError(message)
        return json.loads(response.read())
    finally:
        connection.close()


def _pinned_revision(response: dict[str, object]) -> str:
    """Read and validate one immutable Hub revision.

    Args:
        response: Decoded response fields.

    Returns:
        And validate one immutable Hub revision.

    Raises:
        ValueError: Hugging Face did not return an immutable model revision.

    """
    resolved_revision = response.get("sha")
    if not isinstance(resolved_revision, str) or not _COMMIT_PATTERN.fullmatch(resolved_revision):
        message = "Hugging Face did not return an immutable model revision"
        raise ValueError(message)
    return resolved_revision


def _sibling_filenames(response: dict[str, object]) -> set[str]:
    """Read the model repository filenames advertised by the Hub API.

    Args:
        response: Decoded response fields.

    Returns:
        The model repository filenames advertised by the Hub API.

    """
    siblings = response.get("siblings")
    if not isinstance(siblings, list):
        return set()
    filenames: set[str] = set()
    for sibling_value in cast("list[object]", siblings):
        if isinstance(sibling_value, dict):
            filename = cast("dict[str, object]", sibling_value).get("rfilename")
            if isinstance(filename, str):
                filenames.add(filename)
    return filenames


def _remote_payloads(
    model_path: str,
    resolved_revision: str,
    filenames: set[str],
    token: str | None,
) -> list[tuple[str, object]]:
    """Read the remote checkpoint files that may declare quantization.

    Args:
        model_path: Path of the model.
        resolved_revision: Revision of the resolved.
        filenames: Names of the files.
        token: Hugging Face access token or token text.

    Returns:
        The remote checkpoint files that may declare quantization.

    Raises:
        FileNotFoundError: Model configuration was not found.

    """
    payloads: list[tuple[str, object]] = []
    for filename in QUANTIZATION_CONFIG_FILENAMES:
        if filenames and filename not in filenames:
            continue
        file_path = f"/{model_path}/resolve/{resolved_revision}/{quote(filename, safe='')}"
        payload = _json_request(file_path, token, is_missing_allowed=True)
        if payload is not None:
            payloads.append((filename, payload))
    if not payloads:
        message = "Model configuration was not found"
        raise FileNotFoundError(message)
    return payloads


def read_remote_metadata(model: str, revision: str, token: str | None) -> tuple[str, list[tuple[str, object]]]:
    """Resolve one immutable Hub revision and read its small config files.

    Args:
        model: Model name or local checkpoint path.
        revision: Model revision to use.
        token: Hugging Face access token or token text.

    Returns:
        One immutable Hub revision and read its small config files.

    """
    model_path = quote(model, safe="/")
    revision_path = quote(revision, safe="")
    metadata_path = f"/api/models/{model_path}/revision/{revision_path}"
    response = _mapping(_json_request(metadata_path, token))
    resolved_revision = _pinned_revision(response)
    return resolved_revision, _remote_payloads(
        model_path,
        resolved_revision,
        _sibling_filenames(response),
        token,
    )


__all__ = ["read_remote_metadata"]
