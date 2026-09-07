"""Telemetry initialization and shutdown."""

from __future__ import annotations

import logging
from .sentry import initialize_sentry, shutdown_sentry
from src.runtime.environment import read_environment_text
from config.runtime.telemetry import AXIOM_API_TOKEN, SENTRY_DSN
from .open_telemetry import initialize_open_telemetry, shutdown_open_telemetry

logger = logging.getLogger(__name__)


def initialize_telemetry() -> None:
    """Activate configured telemetry backends. Idempotent."""
    if read_environment_text("AXIOM_API_TOKEN", AXIOM_API_TOKEN):
        initialize_open_telemetry()
    else:
        logger.info("Axiom/OTel disabled (AXIOM_API_TOKEN not set)")

    if read_environment_text("SENTRY_DSN", SENTRY_DSN):
        initialize_sentry()
    else:
        logger.info("Sentry disabled (SENTRY_DSN not set)")


def shutdown_telemetry() -> None:
    """Flush and shutdown all telemetry backends. Idempotent."""
    shutdown_sentry()
    shutdown_open_telemetry()


__all__ = ["initialize_telemetry", "shutdown_telemetry"]
