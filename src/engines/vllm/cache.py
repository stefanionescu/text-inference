"""Non-preemptive vLLM prefix-cache reset coordination."""

from __future__ import annotations

import time
from typing import Protocol
import asyncio
import logging

from config.runtime.cache import CACHE_RESET_RETRY_SECONDS

logger = logging.getLogger(__name__)


class CacheResetEngine(Protocol):
    """Engine behavior required by cache reset coordination."""

    async def reset_caches(self, reason: str) -> bool:
        """Attempt a non-preemptive prefix-cache reset.

        Args:
            reason: Trigger label that `CacheResetCoordinator.try_reset` passes through unchanged.

        Returns:
            True after a reset; False makes the coordinator schedule a retry.

        Raises:
            NotImplementedError: This stub always raises; the coordinator calls the real engine method.

        """
        raise NotImplementedError(reason)


class CacheResetCallback(Protocol):
    """Callable cache-reset behavior used by the reset daemon."""

    async def __call__(
        self,
        reason: str,
        *,
        is_rate_limit_bypassed: bool = False,
    ) -> bool:
        """Attempt one coordinated cache reset.

        Args:
            reason: `timer` for a periodic reset, or `declined_retry` after a declined or failed attempt.
            is_rate_limit_bypassed: Whether the reset skips the local interval check; the daemon always passes True.

        Returns:
            True after a reset. The daemon ignores this value.

        Raises:
            NotImplementedError: This stub always raises; `RuntimeDependencies` supplies the callback.

        """
        raise NotImplementedError(reason, is_rate_limit_bypassed)


class CacheResetCoordinator:
    """Rate-limit resets and retry resets declined by active requests."""

    def __init__(self, reset_interval_seconds: float) -> None:
        """Initialize cache reset coordination state.

        Args:
            reset_interval_seconds: Minimum time between resets; zero or less disables the daemon and the rate limit.

        """
        self._reset_interval_seconds = max(0.0, float(reset_interval_seconds))
        self._lock = asyncio.Lock()
        self._reschedule_event = asyncio.Event()
        self._last_reset = time.monotonic()
        self._retry_at: float | None = None
        self._last_outcome = "idle"
        self._daemon_task: asyncio.Task[None] | None = None

    @property
    def last_outcome(self) -> str:
        """Return the latest reset, skip, decline, or failure outcome."""
        return self._last_outcome

    async def try_reset(
        self,
        engine: CacheResetEngine,
        reason: str,
        *,
        is_rate_limit_bypassed: bool = False,
    ) -> bool:
        """Attempt a non-preemptive reset after applying the local rate limit.

        Args:
            engine: Engine whose `reset_caches` this method calls under the coordinator lock.
            reason: Trigger label written to the logs and passed to the engine.
            is_rate_limit_bypassed: Whether to skip the interval check, as the daemon and the last client disconnect do.

        Returns:
            True after a reset; False when the attempt is rate limited, declined, or failed.

        """
        async with self._lock:
            now = time.monotonic()
            interval = self._reset_interval_seconds
            if not is_rate_limit_bypassed and interval > 0 and (now - self._last_reset) < interval:
                self._last_outcome = "rate_limited"
                logger.info("cache reset skipped reason=%s outcome=rate_limited", reason)
                return False
            try:
                is_reset = await engine.reset_caches(reason)
            except Exception:
                self._schedule_retry("failure")
                logger.exception("cache reset failed reason=%s retry_seconds=%s", reason, CACHE_RESET_RETRY_SECONDS)
                is_reset = False
            else:
                if is_reset:
                    self._last_reset = time.monotonic()
                    self._retry_at = None
                    self._last_outcome = "reset"
                    self._reschedule_event.set()
                    logger.info("cache reset completed reason=%s", reason)
                else:
                    self._schedule_retry("declined")
                    logger.info(
                        "cache reset skipped reason=%s outcome=declined retry_seconds=%s",
                        reason,
                        CACHE_RESET_RETRY_SECONDS,
                    )
            return is_reset

    def _schedule_retry(self, outcome: str) -> None:
        """Schedule one bounded retry after a declined or failed reset.

        Args:
            outcome: `declined` or `failure`, stored as the latest outcome.

        """
        self._last_outcome = outcome
        self._retry_at = time.monotonic() + CACHE_RESET_RETRY_SECONDS
        self._reschedule_event.set()

    def start_daemon(self, reset_callback: CacheResetCallback) -> None:
        """Start the periodic daemon once when resets are enabled.

        Args:
            reset_callback: Callable that the daemon awaits for each periodic or retry attempt.

        """
        if self._daemon_task and not self._daemon_task.done():
            return
        if self._reset_interval_seconds <= 0:
            return
        self._daemon_task = asyncio.create_task(self._daemon_loop(reset_callback))

    def _seconds_until_attempt(self) -> float:
        """Return the delay until the next periodic or retry attempt.

        Returns:
            The delay until the next periodic or retry attempt.

        """
        now = time.monotonic()
        if self._retry_at is not None:
            return max(0.0, self._retry_at - now)
        return max(0.0, self._reset_interval_seconds - (now - self._last_reset))

    async def _daemon_loop(self, reset_callback: CacheResetCallback) -> None:
        """Run periodic resets and fixed-delay retries without a tight loop.

        Args:
            reset_callback: Callable awaited each time the wait times out, with the rate limit bypassed.

        """
        logger.info("cache reset daemon started interval=%ss", self._reset_interval_seconds)
        while True:
            self._reschedule_event.clear()
            delay = self._seconds_until_attempt()
            try:
                await asyncio.wait_for(self._reschedule_event.wait(), timeout=delay)
            except TimeoutError:
                reason = "declined_retry" if self._retry_at is not None else "timer"
                await reset_callback(reason, is_rate_limit_bypassed=True)

    async def stop_daemon(self) -> None:
        """Cancel and await the cache daemon before engine shutdown.

        Raises:
            outcome: The daemon task ended with an exception other than cancellation.

        """
        task = self._daemon_task
        self._daemon_task = None
        if task is None:
            return
        task.cancel()
        outcome = (await asyncio.gather(task, return_exceptions=True))[0]
        if isinstance(outcome, BaseException) and not isinstance(outcome, asyncio.CancelledError):
            raise outcome


__all__ = ["CacheResetCallback", "CacheResetCoordinator", "CacheResetEngine"]
