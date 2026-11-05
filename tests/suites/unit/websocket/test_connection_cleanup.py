"""Connection teardown retains session ownership when the receiver fails."""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
from unittest.mock import Mock, AsyncMock

import pytest

from src.websocket import endpoint
from src.runtime.dependencies import RuntimeDependencies

if TYPE_CHECKING:
    from src.session.state import SessionState


@pytest.mark.parametrize("exception_type", [RuntimeError, LookupError])
def test_receiver_failure_cleanup(
    exception_type: type[Exception],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Abort active engine work and close state after handled or escaping failures."""
    websocket = Mock(client=None, send_text=AsyncMock())
    dependencies = Mock(spec=RuntimeDependencies)
    dependencies.engine = AsyncMock()
    dependencies.connections.active_connections = {websocket}
    dependencies.connections.disconnect = AsyncMock()
    dependencies.clear_caches_on_disconnect = AsyncMock()
    lifecycle = Mock(stop=AsyncMock(), has_idle_timed_out=Mock(return_value=False))
    states: list[SessionState] = []

    async def receive(*_arguments: object, state: SessionState) -> None:
        """Simulate a receiver failing with tracked generation still active."""
        state.active_request_id = "active-generation"
        state.lifecycle_state = "running"
        states.append(state)
        message = "receiver failed"
        raise exception_type(message)

    monkeypatch.setattr(endpoint, "_prepare_connection", AsyncMock(return_value=True))
    monkeypatch.setattr(endpoint, "_start_lifecycle", Mock(return_value=lifecycle))
    monkeypatch.setattr(endpoint, "_create_rate_limiters", Mock(return_value=(Mock(), Mock())))
    monkeypatch.setattr(endpoint, "run_receiver", receive)
    if exception_type is LookupError:
        with pytest.raises(LookupError, match="receiver failed"):
            asyncio.run(endpoint.handle_websocket_connection(websocket, dependencies))
    else:
        asyncio.run(endpoint.handle_websocket_connection(websocket, dependencies))
    dependencies.engine.abort.assert_awaited_once_with("active-generation")
    dependencies.connections.disconnect.assert_awaited_once_with(websocket)
    assert states[0].lifecycle_state == "closed"
    assert states[0].active_request_id is None
