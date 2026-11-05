"""Server, connection, and client error types for test helpers."""

from .client import TestClientError
from .server import ServerError
from .stream import StreamError
from .capacity import ServerAtCapacityError
from .rate_limit import RateLimitError
from .validation import ValidationError
from .idle_timeout import IdleTimeoutError
from .input_closed import InputClosedError
from .message_parse import MessageParseError
from .authentication import AuthenticationError
from .internal_server import InternalServerError
from .invalid_message import InvalidMessageError
from .prompt_selection import PromptSelectionError
from .closed_connection import ConnectionClosedError
from .rejected_connection import ConnectionRejectedError
from .websocket_connection import WebSocketConnectionError

__all__ = [
    "AuthenticationError",
    "ConnectionClosedError",
    "ConnectionRejectedError",
    "IdleTimeoutError",
    "InputClosedError",
    "InternalServerError",
    "InvalidMessageError",
    "MessageParseError",
    "PromptSelectionError",
    "RateLimitError",
    "ServerAtCapacityError",
    "ServerError",
    "StreamError",
    "TestClientError",
    "ValidationError",
    "WebSocketConnectionError",
]
