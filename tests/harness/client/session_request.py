"""Connection and profile inputs that every interactive test client needs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionRequest:
    """Where a client connects, how it authenticates, and which profile it starts.

    Attributes:
        server_url: WebSocket server address for the session.
        api_key: Explicit API key for the session; None reads the `API_KEY` environment variable.
        gender: Gender that selects the prompt profile.
        personality: Personality that selects the prompt profile.
        timeout_seconds: Time limit in seconds for each message exchange.

    """

    server_url: str
    api_key: str | None
    gender: str
    personality: str
    timeout_seconds: float


__all__ = ["SessionRequest"]
