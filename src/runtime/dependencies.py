"""Runtime dependency dataclasses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from dataclasses import dataclass

from src.telemetry.instruments import get_metrics

if TYPE_CHECKING:
    from fastapi import WebSocket

    from src.runtime.config import ApplicationSettings
    from src.session.runtime import SessionRuntime
    from src.engines.protocol import Engine
    from src.tokens.tokenizer import ThreadSafeTokenizer
    from src.engines.vllm.cache import CacheResetCoordinator


class ConnectionRegistryProtocol(Protocol):
    """Connection registry behavior required by request runtime.

    Attributes:
        active_connections: Active connections.

    """

    active_connections: set[WebSocket]

    async def connect(self, websocket: WebSocket) -> bool:
        """Admit a WebSocket connection.

        Args:
            websocket: WebSocket connection of the client.

        Returns:
            Whether the check passes.

        Raises:
            NotImplementedError: The backend does not implement this call.

        """
        raise NotImplementedError(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Release a WebSocket connection.

        Args:
            websocket: WebSocket connection of the client.

        Raises:
            NotImplementedError: The backend does not implement this call.

        """
        raise NotImplementedError(websocket)


@dataclass(slots=True)
class RuntimeDependencies:
    """Process-wide runtime services initialized during startup.

    Attributes:
        connections: Registry of open connections.
        session_runtime: Session runtime.
        engine: Inference engine that serves the request.
        cache_reset_coordinator: Cache reset coordinator.
        tokenizer: Tokenizer to use.
        settings: Application settings.

    """

    connections: ConnectionRegistryProtocol
    session_runtime: SessionRuntime
    engine: Engine
    cache_reset_coordinator: CacheResetCoordinator | None
    tokenizer: ThreadSafeTokenizer
    settings: ApplicationSettings

    def can_reset_cache(self) -> bool:
        """Return whether engine cache reset is available.

        Returns:
            Whether engine cache reset is available.

        """
        return self.engine.can_reset_cache and self.cache_reset_coordinator is not None

    async def reset_engine_caches(
        self,
        reason: str,
        *,
        is_rate_limit_bypassed: bool = False,
    ) -> bool:
        """Reset engine caches when the runtime supports it.

        Args:
            reason: Reason text to report.
            is_rate_limit_bypassed: Whether rate limit is bypassed.

        Returns:
            Whether the check passes.

        """
        coordinator = self.cache_reset_coordinator
        if coordinator is None:
            return False
        is_reset = await coordinator.try_reset(
            self.engine,
            reason,
            is_rate_limit_bypassed=is_rate_limit_bypassed,
        )
        metrics = get_metrics()
        outcome = coordinator.last_outcome
        attributes = {"reason": reason, "outcome": outcome}
        if is_reset:
            metrics.cache_resets_total.add(1, attributes)
        elif outcome == "failure":
            metrics.cache_reset_failures_total.add(1, attributes)
        else:
            metrics.cache_reset_skips_total.add(1, attributes)
        return is_reset

    async def clear_caches_on_disconnect(self) -> None:
        """Clear engine caches after all clients disconnect."""
        reason = "all_clients_disconnected"
        if self.can_reset_cache():
            await self.reset_engine_caches(reason, is_rate_limit_bypassed=True)

    def start_cache_reset_daemon(self) -> None:
        """Start the cache reset daemon when supported."""
        coordinator = self.cache_reset_coordinator
        if not self.can_reset_cache() or coordinator is None:
            return

        coordinator.start_daemon(self.reset_engine_caches)

    async def shutdown(self) -> None:
        """Stop cache coordination before shutting down the engine."""
        coordinator = self.cache_reset_coordinator
        if coordinator is not None:
            await coordinator.stop_daemon()
        await self.engine.shutdown()


__all__ = ["ConnectionRegistryProtocol", "RuntimeDependencies"]
