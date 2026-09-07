"""Shared pytest configuration for the repository test suite."""

from __future__ import annotations

import os

# Keep test runs deterministic/noiseless even when developer shells export
# production telemetry credentials.
os.environ.pop("AXIOM_API_TOKEN", None)
os.environ.pop("SENTRY_DSN", None)
os.environ["OTEL_SDK_DISABLED"] = "true"
