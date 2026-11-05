"""Unit tests for non-preemptive vLLM cache coordination."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
import asyncio
from functools import partial
from dataclasses import field, dataclass
from unittest.mock import AsyncMock

from src.engines.vllm import cache as cache_module
from src.engines.vllm.cache import CacheResetCoordinator
from src.websocket.endpoint import ConnectionFinalization, clear_after_last_disconnect
from src.engines.vllm.engine import VLLMEngine
from src.runtime.dependencies import RuntimeDependencies

if TYPE_CHECKING:
    from typing import Any

    import pytest
    from fastapi import WebSocket

    from src.runtime.config import ApplicationSettings
    from src.session.runtime import SessionRuntime
    from src.engines.protocol import Engine
    from src.tokens.tokenizer import ThreadSafeTokenizer
    from src.engines.vllm.cache import CacheResetEngine
    from src.runtime.dependencies import ConnectionRegistryProtocol


@dataclass
class _ResetEngine:
    """Return configured reset outcomes and retain attempt reasons.

    Attributes:
        outcomes: Outcomes that the test double records.
        reasons: Reasons that the record collects.
        attempted: Event that is set after the first attempt.

    """

    outcomes: list[bool | Exception]
    reasons: list[str] = field(default_factory=list)
    attempted: asyncio.Event = field(default_factory=asyncio.Event)

    async def reset_caches(self, reason: str) -> bool:
        """Return or raise the next configured reset outcome.

        Args:
            reason: Trigger label that this test double records.

        Returns:
            The next configured bool outcome.

        Raises:
            outcome: The next configured outcome is an exception.

        """
        self.reasons.append(reason)
        outcome = self.outcomes.pop(0)
        if len(self.reasons) > 1:
            self.attempted.set()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@dataclass
class _PrefixResetRuntime:
    """Record vLLM prefix-reset options.

    Attributes:
        requests: Option pairs from each recorded reset.

    """

    requests: list[tuple[bool, bool]] = field(default_factory=list)

    async def reset_prefix_cache(
        self,
        *,
        reset_running_requests: bool = False,
        reset_connector: bool = False,
    ) -> bool:
        """Record one prefix reset and reject preemptive requests.

        Args:
            reset_running_requests: Preemption flag; True fails the test.
            reset_connector: Connector flag that the test records.

        Returns:
            Always True, because the recorded reset succeeds.

        Raises:
            AssertionError: Test received a preemptive reset.

        """
        self.requests.append((reset_running_requests, reset_connector))
        if reset_running_requests:
            message = "test received a preemptive reset"
            raise AssertionError(message)
        return True


def test_cache_rate_limit() -> None:
    """Test forced disconnect resets bypass the periodic rate limit."""

    async def scenario() -> tuple[bool, bool, list[str]]:
        engine = _ResetEngine([True])
        coordinator = CacheResetCoordinator(600.0)
        is_forced_reset = await coordinator.try_reset(
            cast("CacheResetEngine", engine),
            "disconnect",
            is_rate_limit_bypassed=True,
        )
        is_periodic_reset = await coordinator.try_reset(cast("CacheResetEngine", engine), "timer")
        return is_forced_reset, is_periodic_reset, engine.reasons

    assert asyncio.run(scenario()) == (True, False, ["disconnect"])


def test_vllm_nonpreemptive_reset() -> None:
    """Test the vLLM adapter explicitly requests non-preemptive reset behavior."""
    runtime = _PrefixResetRuntime()
    engine = VLLMEngine(
        cast("Any", runtime),
        cast("Any", object()),
    )

    assert asyncio.run(engine.reset_caches("timer"))
    assert runtime.requests == [(False, False)]


def test_periodic_cache_timer() -> None:
    """Test the cache daemon triggers its ten-minute-style timer."""

    async def scenario() -> tuple[str, bool]:
        attempted = asyncio.Event()
        coordinator = CacheResetCoordinator(0.01)

        async def reset_caches(
            reason: str,
            *,
            is_rate_limit_bypassed: bool = False,
        ) -> bool:
            attempted.set()
            return reason == "timer" and is_rate_limit_bypassed

        coordinator.start_daemon(reset_caches)
        await asyncio.wait_for(attempted.wait(), timeout=1.0)
        await coordinator.stop_daemon()
        return coordinator.last_outcome, attempted.is_set()

    assert asyncio.run(scenario()) == ("idle", True)


def test_declined_reset_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a declined reset retries once after the fixed delay.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.

    """
    monkeypatch.setattr(cache_module, "CACHE_RESET_RETRY_SECONDS", 0.01)

    async def scenario() -> tuple[list[str], str]:
        engine = _ResetEngine([False, True])
        coordinator = CacheResetCoordinator(600.0)
        reset_engine = cast("CacheResetEngine", engine)
        assert not await coordinator.try_reset(
            reset_engine,
            "disconnect",
            is_rate_limit_bypassed=True,
        )

        coordinator.start_daemon(partial(coordinator.try_reset, reset_engine))
        await asyncio.wait_for(engine.attempted.wait(), timeout=1.0)
        await coordinator.stop_daemon()
        return engine.reasons, coordinator.last_outcome

    reasons, outcome = asyncio.run(scenario())
    assert reasons == ["disconnect", "declined_retry"]
    assert outcome == "reset"


def test_disconnect_client_counts() -> None:
    """Test only the last connected client triggers immediate reset."""

    async def scenario() -> int:
        reset = AsyncMock()
        runtime = cast("RuntimeDependencies", cast("object", SimpleNamespace(clear_caches_on_disconnect=reset)))
        finalization = ConnectionFinalization(
            websocket=cast("WebSocket", object()),
            runtime_dependencies=runtime,
            lifecycle=None,
            state=None,
            is_admitted=True,
        )
        await clear_after_last_disconnect(finalization, 1)
        await clear_after_last_disconnect(finalization, 0)
        return reset.await_count

    assert asyncio.run(scenario()) == 1


def test_shutdown_order() -> None:
    """Test cache coordination stops before the engine shuts down."""

    async def scenario() -> list[str]:
        events: list[str] = []
        coordinator = SimpleNamespace(stop_daemon=AsyncMock(side_effect=lambda: events.append("cache")))
        engine = SimpleNamespace(shutdown=AsyncMock(side_effect=lambda: events.append("engine")))
        runtime = RuntimeDependencies(
            connections=cast("ConnectionRegistryProtocol", object()),
            session_runtime=cast("SessionRuntime", object()),
            engine=cast("Engine", cast("object", engine)),
            cache_reset_coordinator=cast("CacheResetCoordinator", cast("object", coordinator)),
            tokenizer=cast("ThreadSafeTokenizer", object()),
            settings=cast("ApplicationSettings", object()),
        )
        await runtime.shutdown()
        return events

    assert asyncio.run(scenario()) == ["cache", "engine"]
