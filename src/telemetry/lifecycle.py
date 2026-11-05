"""Telemetry initialization."""

from __future__ import annotations

import logging

from src.runtime.environment import read_environment_text
from config.runtime.telemetry import SENTRY_DSN, AXIOM_API_TOKEN

from .sentry import initialize_sentry
from .open_telemetry import initialize_open_telemetry

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


__all__ = ["initialize_telemetry"]
