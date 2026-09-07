"""Timeouts and buffering configuration.

Centralizes generation timeouts and executor buffering sizes.
Runtime environment overrides are resolved under ``src.runtime``.
"""

# Text generation hard timeout in seconds
GENERATION_TIMEOUT_SECONDS = 60.0

# Timeout for fetching license metadata from HuggingFace API
HUGGING_FACE_LICENSE_TIMEOUT_SECONDS = 5.0


__all__ = [
    "GENERATION_TIMEOUT_SECONDS",
    "HUGGING_FACE_LICENSE_TIMEOUT_SECONDS",
]
