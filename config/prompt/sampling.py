"""Sampling defaults for models.

This module defines the default sampling parameters used during text
generation. These control the randomness and diversity of outputs.

Sampling Parameters:
    temperature: Controls randomness (0=deterministic, 1=more random)
        Higher values produce more creative but less coherent outputs.

    top_p (nucleus sampling): Cumulative probability threshold
        Only considers tokens whose cumulative probability <= top_p.
        Lower values (0.8-0.95) reduce unlikely token selection.

    top_k: Maximum number of tokens to consider
        0 = disabled, 30-50 is common for interactive applications.

    min_p: Minimum probability threshold
        Filters out tokens below this probability, which removes unlikely
        tokens with less restriction than top_k.

    repetition_penalty: Penalty for repeating tokens (1.0 = no penalty)
        Values > 1.0 reduce repetition, 1.05-1.15 is typical.

    presence_penalty: Penalty for tokens already in context
        Encourages talking about new topics.

    frequency_penalty: Penalty based on token frequency in context
        Reduces repetition of the same words/phrases.

Stop Sequences:
    INFERENCE_STOP contains tokens that terminate generation. These are
    model-specific and cover various message formats (ChatML, Gemma, Kimi, etc.)

All values can be overridden via environment variables or per-request.
"""

from __future__ import annotations

# ============================================================================
# Default Sampling Parameters
# ============================================================================
# These are server defaults. Clients can override per-request within limits.

TEMPERATURE = 0.8
TOP_P = 0.95
TOP_K = 30
MIN_P = 0.0
REPETITION_PENALTY = 1.0
PRESENCE_PENALTY = 0.0
FREQUENCY_PENALTY = 0.0


# ============================================================================
# Logit Bias (Token Suppression)
# ============================================================================
# Discourage certain tokens/text patterns from being generated.
# -100 effectively bans the token entirely.
# This helps avoid unwanted punctuation, filler words, and expressions.

LOGIT_BIAS: dict[str, float] = {
    "*": -100,  # Markdown emphasis
    "(": -100,  # Parenthetical asides
    ")": -100,
    "~": -100,  # Tildes
    " - ": -100,  # Dashes
    "-": -100,
    "Mmh": -100,  # Filler sounds
    "hmm": -100,
    "…": -100,  # Ellipsis
    "Damn": -100,  # Profanity
    "stud": -100,  # Unwanted terms
}

# ============================================================================
# Stop Sequences
# ============================================================================
# Tokens that terminate generation. Covers multiple message formats:
# - ChatML: <|im_end|>, <|assistant|>, <|user|>
# - Gemma 1/2: <end_of_turn>, <start_of_turn>
# - Gemma 3: <|eot_id|>, <|start_header_id|>
# - Kimi: <|im_user|>, <|im_system|>, [EOS], [EOT]
# - DeepSeek V2/V3: Fullwidth vertical bars and "User:" prefix
# - Mistral: [INST], [/INST]

INFERENCE_STOP = [
    # ChatML format (including partial tokenization variants)
    "<|im_end|>",
    "<|im_end|",
    "|im_end|>",
    "|im_end|",
    "<|im_start|>",
    "<|im_start|",
    "<|assistant|>",
    "<|user|>",
    "<|end|>",
    # Gemma 1/2 format
    "<end_of_turn>",
    "<start_of_turn>",
    # Gemma 3 format
    "<|eot_id|>",
    "<|start_header_id|>",
    # Kimi / Kimi Linear format
    "<|im_user|>",
    "<|im_system|>",
    "[EOS]",
    "[EOT]",
    # DeepSeek V2/V3 format (uses fullwidth vertical bars)
    "<\uff5cend\u2581of\u2581sentence\uff5c>",
    "<\uff5cbegin\u2581of\u2581sentence\uff5c>",
    "User:",  # DeepSeek uses "User:" prefix
    # Mistral format
    "[INST]",
    "[/INST]",
    # General
    "[SYSTEM_PROMPT]",
    "[/SYSTEM_PROMPT]",
]

__all__ = [
    "FREQUENCY_PENALTY",
    "INFERENCE_STOP",
    "LOGIT_BIAS",
    "MIN_P",
    "PRESENCE_PENALTY",
    "REPETITION_PENALTY",
    "TEMPERATURE",
    "TOP_K",
    "TOP_P",
]
