"""Token, history, and concurrency limits configuration.

This module defines the various limits that control resource usage and
protect against abuse. Limits are organized into categories:

Context Limits:
    - MAXIMUM_CONTEXT_LENGTH: Maximum input context length (tokens)
    - MAXIMUM_OUTPUT_TOKENS: Maximum generation length (tokens)
    - HISTORY_MAX_TOKENS: Threshold that triggers history trimming (tokens)
    - TRIMMED_HISTORY_LENGTH: Target length after trimming (tokens)
    - USER_UTTERANCE_MAX_TOKENS: Maximum user utterance (tokens)
    - PROMPT_MAX_TOKENS: Maximum profile prompt (tokens)

Runtime environment overrides are resolved under ``src.runtime``.
"""

# ============================================================================
# Context Window Limits
# ============================================================================
# These define the maximum token budget for different components.
# Total budget breakdown: 1500 profile + 3000 history + 500 user + 25 buffer

# Max tokens allowed for incoming prompts (provided by clients)
PROMPT_MAX_TOKENS = 1500

# History and user limits (token counts from active tokenizer path)
# HISTORY_MAX_TOKENS: threshold that triggers trimming
HISTORY_MAX_TOKENS = 3000
USER_UTTERANCE_MAX_TOKENS = 500

# Percentage of HISTORY_MAX_TOKENS to retain after trimming
HISTORY_RETENTION_PERCENTAGE = 66

CONTEXT_BUFFER = 25

MAXIMUM_CONTEXT_LENGTH = 5025
MAXIMUM_OUTPUT_TOKENS = 150  # Max generation tokens

# TRIMMED_HISTORY_LENGTH: target length after trimming (must be < HISTORY_MAX_TOKENS)
TRIMMED_HISTORY_LENGTH = 1980

# Optional tiny coalescer: 0 = off; if you ever want to reduce packet spam set 5-15ms
STREAM_FLUSH_MILLISECONDS = 0.0

# Maximum concurrent WebSocket connections
# Validated at runtime by src/runtime/validation.py
MAX_CONCURRENT_CONNECTIONS: int | None = None

# ============================================================================
# Sampling Clamps
# ============================================================================
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 1.2
TOP_P_MIN = 0.6
TOP_P_MAX = 1.0
TOP_K_MIN = 0
TOP_K_MAX = 60
MIN_P_LOWER = 0.0
MIN_P_MAX = 0.20
REPETITION_PENALTY_MIN = 1.0
REPETITION_PENALTY_MAX = 1.3
PRESENCE_PENALTY_MIN = 0.0
PRESENCE_PENALTY_MAX = 0.5
FREQUENCY_PENALTY_MIN = 0.0
FREQUENCY_PENALTY_MAX = 0.5

# Personality validation
PERSONALITY_MAX_LENGTH = 20

__all__ = [
    "CONTEXT_BUFFER",
    "FREQUENCY_PENALTY_MAX",
    "FREQUENCY_PENALTY_MIN",
    "HISTORY_MAX_TOKENS",
    "HISTORY_RETENTION_PERCENTAGE",
    "MAXIMUM_CONTEXT_LENGTH",
    "MAXIMUM_OUTPUT_TOKENS",
    "MAX_CONCURRENT_CONNECTIONS",
    "MIN_P_LOWER",
    "MIN_P_MAX",
    "PERSONALITY_MAX_LENGTH",
    "PRESENCE_PENALTY_MAX",
    "PRESENCE_PENALTY_MIN",
    "PROMPT_MAX_TOKENS",
    "REPETITION_PENALTY_MAX",
    "REPETITION_PENALTY_MIN",
    "STREAM_FLUSH_MILLISECONDS",
    "TEMPERATURE_MAX",
    "TEMPERATURE_MIN",
    "TOP_K_MAX",
    "TOP_K_MIN",
    "TOP_P_MAX",
    "TOP_P_MIN",
    "TRIMMED_HISTORY_LENGTH",
    "USER_UTTERANCE_MAX_TOKENS",
]
