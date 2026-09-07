"""Unit tests for inference engine output adapters."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from src.runtime import bootstrap
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, Mock
from src.engines.trt.engine import TRTEngine
from src.engines.protocol import SamplingParametersRequest
from tests.harness.environment.tokenizer import build_local_tokenizer
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS

if TYPE_CHECKING:
    import pytest
    from collections.abc import AsyncIterator
    from src.engines.protocol import EngineOutput


@dataclass
class _FakeCompletion:
    text: str
    token_ids: list[int]


@dataclass
class _FakeChunk:
    outputs: list[_FakeCompletion]
    finished: bool


@dataclass
class _FakeGeneration:
    chunks: list[_FakeChunk]
    is_aborted: bool = False

    def __aiter__(self) -> AsyncIterator[_FakeChunk]:
        """Iterate over test generation chunks."""

        async def _chunks() -> AsyncIterator[_FakeChunk]:
            for chunk in self.chunks:
                yield chunk

        return _chunks()

    def abort(self) -> None:
        """Record cancellation."""
        self.is_aborted = True


@dataclass
class _FakeLLM:
    generation: _FakeGeneration
    is_shutdown_called: bool = False

    def generate_async(self, prompt: str, sampling_params: object, *, streaming: bool) -> _FakeGeneration:
        """Return the configured asynchronous generation."""
        _ = (prompt, sampling_params, streaming)
        return self.generation

    def shutdown(self) -> None:
        """Record runtime shutdown."""
        self.is_shutdown_called = True


class _FakeSamplingParams:
    """Stand in for the selected backend's exact sampling class."""

    def __init__(self, **values: object) -> None:
        """Store constructor values."""
        self.values = values


def test_trt_stream_outputs() -> None:
    """Test TRT generation exposes cumulative text, tokens, and completion state."""
    generation = _FakeGeneration(
        chunks=[
            _FakeChunk(outputs=[_FakeCompletion(text="hello", token_ids=[1])], finished=False),
            _FakeChunk(outputs=[_FakeCompletion(text="hello world", token_ids=[1, 2])], finished=True),
        ],
    )
    llm = _FakeLLM(generation)
    engine = TRTEngine(llm, _FakeSamplingParams, 8)
    sampling_parameters = object()

    async def _collect() -> list[EngineOutput]:
        return [
            output
            async for output in engine.generate_stream(
                "prompt",
                sampling_parameters,
                "request",
            )
        ]

    outputs = asyncio.run(_collect())

    assert [(output.text, output.token_ids, output.is_finished) for output in outputs] == [
        ("hello", [1], False),
        ("hello world", [1, 2], True),
    ]


def test_trt_aborts_generation() -> None:
    """Test abort cancels the matching in-flight generation."""
    generation = _FakeGeneration(
        chunks=[_FakeChunk(outputs=[_FakeCompletion(text="waiting", token_ids=[7])], finished=False)],
    )
    engine = TRTEngine(_FakeLLM(generation), _FakeSamplingParams, 8)

    async def _abort() -> None:
        stream = engine.generate_stream("prompt", object(), "request")
        await anext(stream)
        await engine.abort("request")
        await stream.aclose()

    asyncio.run(_abort())

    assert generation.is_aborted


def test_trt_shutdown_backend() -> None:
    """Test shutdown releases backend worker resources."""
    llm = _FakeLLM(_FakeGeneration(chunks=[]))
    engine = TRTEngine(llm, _FakeSamplingParams, 8)

    asyncio.run(engine.shutdown())

    assert llm.is_shutdown_called


def test_trt_logit_bias() -> None:
    """Test TRT receives its native dense vocabulary bias vector."""
    engine = TRTEngine(
        _FakeLLM(_FakeGeneration(chunks=[])),
        _FakeSamplingParams,
        5,
    )

    parameters = cast(
        "_FakeSamplingParams",
        engine.create_sampling_parameters(SamplingParametersRequest(logit_bias={1: -100.0, 4: 2.5})),
    )

    assert parameters.values["embedding_bias"] == [0.0, -100.0, 0.0, 0.0, 2.5]


def test_trt_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bootstrap a TRT adapter without creating a cache reset coordinator."""
    engine = TRTEngine(_FakeLLM(_FakeGeneration(chunks=[])), _FakeSamplingParams, 8)
    tokenizer = build_local_tokenizer()
    monkeypatch.setattr(bootstrap, "_build_tokenizer", AsyncMock(return_value=tokenizer))
    dependencies = asyncio.run(
        bootstrap.build_runtime_dependencies(
            DEFAULT_APPLICATION_SETTINGS,
            connections=Mock(),
            engine_builder=AsyncMock(return_value=engine),
        ),
    )
    assert dependencies.engine is engine
    assert dependencies.cache_reset_coordinator is None
    assert not dependencies.can_reset_cache()
