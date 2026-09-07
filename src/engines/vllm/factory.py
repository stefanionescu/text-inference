"""vLLM 0.25.1 composition root."""

from __future__ import annotations

import asyncio
from .engine import VLLMEngine
from vllm import SamplingParams
from transformers import AutoConfig
from typing import TYPE_CHECKING, cast
from vllm.v1.engine.async_llm import AsyncLLM
from vllm.engine.arg_utils import AsyncEngineArgs
from src.tokens.validation import require_local_model_directory
from src.quantization.vllm.policy import choose_quantization_backend

if TYPE_CHECKING:
    from src.state.settings import ApplicationSettings


async def create_vllm_engine(settings: ApplicationSettings) -> VLLMEngine:
    """Create the vLLM 0.25.1 asynchronous engine."""
    model = require_local_model_directory(cast("str", settings.model.source))
    quantization_format = settings.model.runtime_quantization
    model_config = await asyncio.to_thread(
        AutoConfig.from_pretrained,
        model,
        trust_remote_code=True,
        local_files_only=True,
    )
    model_config_payload = model_config.to_dict()
    quantization_backend = choose_quantization_backend(quantization_format, model_config_payload)

    engine_arguments = AsyncEngineArgs(
        model=str(model),
        trust_remote_code=True,
        tensor_parallel_size=1,
        device_ids=[0],
        max_model_len=settings.session.maximum_sequence_length,
        gpu_memory_utilization=settings.gpu.gpu_memory_fraction,
        enforce_eager=settings.engine.is_eager_execution_enforced,
        quantization=quantization_backend,
        kv_cache_dtype=settings.gpu.key_value_cache_precision,
        language_model_only=True,
    )
    engine = AsyncLLM.from_engine_args(engine_arguments)
    return VLLMEngine(engine, SamplingParams)


__all__ = ["create_vllm_engine"]
