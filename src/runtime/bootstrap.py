"""Runtime dependency bootstrap.

This module eagerly builds all configured runtime services at startup.
Request handlers consume these dependencies directly instead of triggering
lazy singleton initialization at request time.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from .dependencies import RuntimeDependencies
from src.session.runtime import SessionRuntime
from src.tokens.tokenizer import ThreadSafeTokenizer
from src.engines.vllm.cache import CacheResetCoordinator

if TYPE_CHECKING:
    from src.engines.protocol import Engine
    from collections.abc import Awaitable, Callable
    from src.state.settings import ApplicationSettings
    from src.runtime.dependencies import ConnectionRegistryProtocol

    type EngineBuilder = Callable[[ApplicationSettings], Awaitable[Engine]]


async def _build_tokenizer(settings: ApplicationSettings) -> ThreadSafeTokenizer:
    """Build the tokenizer used for prompt budgeting."""
    if not settings.model.source:
        message = "MODEL is required"
        raise RuntimeError(message)
    return await asyncio.to_thread(ThreadSafeTokenizer, settings.model.source)


async def build_runtime_dependencies(
    settings: ApplicationSettings,
    connections: ConnectionRegistryProtocol,
    engine_builder: EngineBuilder,
) -> RuntimeDependencies:
    """Build runtime dependencies eagerly."""
    engine, tokenizer = await asyncio.gather(
        engine_builder(settings),
        _build_tokenizer(settings),
    )

    session_runtime = SessionRuntime(
        settings=settings,
        engine=engine,
        tokenizer=tokenizer,
    )
    cache_reset_coordinator = None
    if engine.can_reset_cache:
        cache_reset_coordinator = CacheResetCoordinator(settings.session.cache_reset_interval_seconds)

    return RuntimeDependencies(
        connections=connections,
        session_runtime=session_runtime,
        settings=settings,
        engine=engine,
        cache_reset_coordinator=cache_reset_coordinator,
        tokenizer=tokenizer,
    )


__all__ = [
    "build_runtime_dependencies",
]
