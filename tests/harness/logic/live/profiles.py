"""Prompt profile registry for interactive sessions."""

from __future__ import annotations

from tests.state import PromptProfile
from tests.harness.client.prompt import normalize_gender
from config.tests.prompts.detailed import PROMPT_PROFILES


class PromptProfileRegistry:
    """Resolve protocol prompt profiles by gender and personality."""

    def read_profiles(self) -> dict[tuple[str, str], PromptProfile]:
        """Return validated prompt profiles keyed by protocol fields.

        Returns:
            Validated prompt profiles keyed by protocol fields.

        Raises:
            ValueError: Prompt profile key `key` does not match its protocol fields.

        """
        profiles: dict[tuple[str, str], PromptProfile] = {}
        for key, payload in PROMPT_PROFILES.items():
            gender = normalize_gender(str(payload["gender"]))
            personality = str(payload["personality"]).strip().lower()
            prompt = str(payload["prompt"])
            if key != (gender, personality):
                message = f"Prompt profile key {key!r} does not match its protocol fields"
                raise ValueError(message)
            profiles[key] = PromptProfile(gender=gender, personality=personality, prompt=prompt)
        return profiles

    def require_profile(self, gender: str, personality: str) -> PromptProfile:
        """Return one exact gender and personality profile.

        Args:
            gender: Name of the gender profile.
            personality: Name of the personality profile.

        Returns:
            One exact gender and personality profile.

        Raises:
            ValueError: Unknown prompt profile '`key`/`key`'. Available: `available`.

        """
        key = (normalize_gender(gender), personality.strip().lower())
        try:
            return self.read_profiles()[key]
        except KeyError as exception:
            available = ", ".join(
                f"{item_gender}/{item_personality}" for item_gender, item_personality in sorted(self.read_profiles())
            )
            message = f"Unknown prompt profile '{key[0]}/{key[1]}'. Available: {available}"
            raise ValueError(message) from exception

    def available_genders(self) -> list[str]:
        """Return unique genders in the prompt profile registry.

        Returns:
            Unique genders in the prompt profile registry.

        """
        return sorted({gender for gender, _ in self.read_profiles()})

    def available_personalities(self) -> list[str]:
        """Return unique personalities in the prompt profile registry.

        Returns:
            Unique personalities in the prompt profile registry.

        """
        return sorted({personality for _, personality in self.read_profiles()})


__all__ = ["PromptProfileRegistry"]
