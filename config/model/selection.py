"""Model reference configuration."""

HF_REPO_PATTERN_TEXT = r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+$"

MODEL: str | None = None


__all__ = [
    "HF_REPO_PATTERN_TEXT",
    "MODEL",
]
