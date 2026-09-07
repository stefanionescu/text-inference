"""Unit tests for shared client, prompt, and live-command contracts."""

from __future__ import annotations

import asyncio
import importlib.util
from dataclasses import fields
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from src.runtime import DEFAULT_APPLICATION_SETTINGS
from src.execution.runner import build_sampling_overrides
from tests.harness.client.cli import build_sampling_payload
from config.tests.defaults import TRANSACTION_TIMEOUT_SECONDS
from tests.harness.client.websocket import build_websocket_url
from tests.harness.logic.live.profiles import PromptProfileRegistry
from tests.harness.logic.live.commands import COMMAND_CALLBACKS, dispatch_command

EXPECTED_TIMEOUT_SECONDS = 120.0

if TYPE_CHECKING:
    from tests.harness.logic.live.client import LiveClient


def test_sanitization_opt_in() -> None:
    """Test clients and server execution leave sanitization disabled by default."""
    sampling = DEFAULT_APPLICATION_SETTINGS.sampling

    assert build_sampling_payload({}) == {}
    assert build_sampling_payload({"sanitize": False}) == {}
    assert build_sampling_payload({"sanitize": True}) == {"sanitize_output": True}
    assert not build_sampling_overrides({}, sampling_settings=sampling)["sanitize_output"]


def test_shared_timeout_default() -> None:
    """Test the common transaction timeout remains 120 seconds."""
    assert TRANSACTION_TIMEOUT_SECONDS == EXPECTED_TIMEOUT_SECONDS


def test_remote_websocket_url() -> None:
    """Test remote HTTPS deployments normalize to secure WebSocket URLs."""
    assert build_websocket_url("https://example.test", api_key="secret") == "wss://example.test/ws"


def test_root_configuration_imports() -> None:
    """Test production and test configuration import only from the root package."""
    assert importlib.util.find_spec("config.runtime") is not None
    assert importlib.util.find_spec("config.tests") is not None
    assert importlib.util.find_spec("src.config") is None
    assert importlib.util.find_spec("tests.config") is None


def test_timing_field_names() -> None:
    """Test runtime settings use full-word timing field suffixes."""
    timing_settings = (
        DEFAULT_APPLICATION_SETTINGS.session,
        DEFAULT_APPLICATION_SETTINGS.timeouts,
        DEFAULT_APPLICATION_SETTINGS.websocket,
    )

    for settings in timing_settings:
        names = {field.name for field in fields(settings)}
        assert not {name for name in names if name.endswith(("_s", "_ms", "_sec", "_secs"))}


def test_prompt_pair_registry() -> None:
    """Test profiles are keyed by protocol gender and personality pairs."""
    registry = PromptProfileRegistry()
    profiles = registry.read_profiles()

    assert profiles
    assert all(key == (profile.gender, profile.personality) for key, profile in profiles.items())
    assert registry.available_genders() == sorted(set(registry.available_genders()))
    assert "warm" in registry.available_personalities()


def test_live_command_set() -> None:
    """Test the live client exposes only the documented slash commands."""
    assert set(COMMAND_CALLBACKS) == {"help", "history", "genders", "personalities", "stats", "stop"}


def test_stats_command_toggle() -> None:
    """Test stats toggles without arguments and rejects command arguments."""

    async def scenario() -> bool:
        client = cast("LiveClient", SimpleNamespace(is_stats_logging_enabled=False))
        registry = PromptProfileRegistry()
        assert not await dispatch_command("stats", client, registry)
        assert not await dispatch_command("stats on", client, registry)
        return client.is_stats_logging_enabled

    assert asyncio.run(scenario())
