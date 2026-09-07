"""Runtime dependency dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol
from src.telemetry.instruments import get_metrics

if TYPE_CHECKING:
    from fastapi import WebSocket
    from src.state.turn import TurnPlan
    from collections.abc import Awaitable
    from src.engines.protocol import Engine
    from src.session.runtime import SessionRuntime
    from src.state.settings import ApplicationSettings
    from src.tokens.tokenizer import ThreadSafeTokenizer
    from src.engines.vllm.cache import CacheResetCoordinator


class ConnectionRegistryProtocol(Protocol):
    """Connection registry behavior required by request runtime."""

    active_connections: set[WebSocket]

    async def connect(self, websocket: WebSocket) -> bool:
        """Admit a WebSocket connection."""
        raise NotImplementedError(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Release a WebSocket connection."""
        raise NotImplementedError(websocket)


class TurnDispatcher(Protocol):
    """Asynchronous turn-dispatch behavior injected into the runtime."""

    def __call__(
        self,
        websocket: WebSocket,
        plan: TurnPlan,
        runtime_dependencies: RuntimeDependencies,
    ) -> Awaitable[None]:
        """Dispatch one validated turn."""
        raise NotImplementedError(websocket, plan, runtime_dependencies)


@dataclass(slots=True)
class RuntimeDependencies:
    """Process-wide runtime services initialized during startup."""

    connections: ConnectionRegistryProtocol
    session_runtime: SessionRuntime
    engine: Engine
    cache_reset_coordinator: CacheResetCoordinator | None
    tokenizer: ThreadSafeTokenizer
    settings: ApplicationSettings
    turn_dispatch: TurnDispatcher | None = None

    def can_reset_cache(self) -> bool:
        """Return whether engine cache reset is available."""
        return self.engine.can_reset_cache and self.cache_reset_coordinator is not None

    async def reset_engine_caches(
        self,
        reason: str,
        *,
        is_rate_limit_bypassed: bool = False,
    ) -> bool:
        """Reset engine caches when the runtime supports it."""
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


__all__ = ["ConnectionRegistryProtocol", "RuntimeDependencies", "TurnDispatcher"]
