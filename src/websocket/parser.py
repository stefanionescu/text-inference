"""Client payload parsing and schema validation for the WebSocket handler.

All client messages must be flat JSON objects with:
    {"type": "...", "v": <protocol_version>, ...fields}

Validation is strict:
- Unknown fields are rejected
- Message schemas are type-specific
- History items are schema-validated
- Protocol version must match server configuration
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated, cast

from pydantic import Field, TypeAdapter, ValidationError

from src.websocket.schemas import EndMessage, PingMessage, PongMessage, TurnMessage, StartMessage, CancelMessage

if TYPE_CHECKING:
    from src.runtime.config import WebSocketSettings

_client_message_model_type = StartMessage | TurnMessage | CancelMessage | PingMessage | PongMessage | EndMessage
_client_message_type = Annotated[
    StartMessage | TurnMessage | CancelMessage | PingMessage | PongMessage | EndMessage,
    Field(discriminator="type"),
]
_MESSAGE_ADAPTER: TypeAdapter[_client_message_model_type] = TypeAdapter(_client_message_type)


def _format_validation_error(exception: ValidationError) -> str:
    """Convert a Pydantic validation error into a concise parser error."""
    errors = exception.errors()
    if not errors:
        return "Message payload failed validation."
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", [])) or "payload"
    message = first.get("msg", "invalid value")
    return f"Invalid payload field '{location}': {message}"


def _json_mapping(value: object) -> dict[str, object]:
    """Return a string-keyed JSON object from unknown parsed JSON."""
    if not isinstance(value, dict):
        return {}
    raw = cast("dict[object, object]", value)
    return {key: item for key, item in raw.items() if isinstance(key, str)}


def _decode_json_mapping(raw: str, websocket_settings: WebSocketSettings) -> dict[str, object]:
    """Decode a raw WebSocket message into a JSON object."""
    raw_text = raw or ""
    raw_size = len(raw_text.encode("utf-8"))
    if raw_size > websocket_settings.maximum_message_bytes:
        message = f"Message exceeds max size ({websocket_settings.maximum_message_bytes} bytes)."
        raise ValueError(message)

    text = raw_text.strip()
    if not text:
        message = "Empty message."
        raise ValueError(message)

    try:
        decoded: object = json.loads(text)
    except json.JSONDecodeError as exception:
        message = "Message must be valid JSON."
        raise ValueError(message) from exception

    if not isinstance(decoded, dict):
        message = "Message must be a JSON object."
        raise TypeError(message)
    return _json_mapping(cast("object", decoded))


def _message_type(payload: dict[str, object]) -> str:
    """Return the normalized client message type."""
    message_type = payload.get("type")
    if not message_type:
        message = "Missing 'type' in message."
        raise ValueError(message)
    return str(message_type).strip().lower()


def _validate_protocol_version(payload: dict[str, object], websocket_settings: WebSocketSettings) -> None:
    """Validate the client protocol version when present."""
    if "v" in payload and payload.get("v") != websocket_settings.protocol_version:
        message = (
            f"Invalid payload field 'v': Value error, unsupported protocol version: {payload.get('v')} "
            f"(expected {websocket_settings.protocol_version})"
        )
        raise ValueError(message)


def parse_client_message(
    raw: str,
    *,
    websocket_settings: WebSocketSettings,
) -> dict[str, object]:
    """Parse and normalize a client WebSocket message.

    Args:
        raw: Raw message string from WebSocket.
        websocket_settings: WebSocket parser limits and protocol version.

    Returns:
        Normalized message dict with 'type' lowercased.

    Raises:
        TypeError: If the decoded JSON payload is not an object.
        ValueError: If message is empty, invalid JSON, or missing type.

    """
    payload = _decode_json_mapping(raw, websocket_settings)
    payload["type"] = _message_type(payload)
    _validate_protocol_version(payload, websocket_settings)
    try:
        validated = _MESSAGE_ADAPTER.validate_python(payload)
    except ValidationError as exception:
        raise ValueError(_format_validation_error(exception)) from exception
    return _json_mapping(cast("object", validated.model_dump(exclude_none=True)))
