"""TensorRT-LLM 1.3.0rc20 public PyTorch backend composition root."""

from __future__ import annotations

import asyncio
from .engine import TRTEngine
from transformers import AutoConfig
from typing import TYPE_CHECKING, cast
from tensorrt_llm.llmapi import KvCacheConfig
from tensorrt_llm import LLM, SamplingParams, logger
from src.tokens.validation import require_local_model_directory

if TYPE_CHECKING:
    from src.state.settings import ApplicationSettings


async def create_trt_engine(settings: ApplicationSettings) -> TRTEngine:
    """Create the TensorRT-LLM 1.3.0rc20 public PyTorch backend."""
    model = require_local_model_directory(cast("str", settings.model.source))
    model_config = await asyncio.to_thread(
        AutoConfig.from_pretrained,
        model,
        trust_remote_code=True,
        local_files_only=True,
    )
    vocab_size = model_config.get_text_config(decoder=True).vocab_size
    if not isinstance(vocab_size, int):
        message = "Model vocabulary size must be an integer"
        raise TypeError(message)

    logger.set_level("info" if settings.engine.is_logging_enabled else "error")
    llm = await asyncio.to_thread(
        LLM,
        model=str(model),
        tokenizer=str(model),
        trust_remote_code=True,
        tensor_parallel_size=1,
        dtype=settings.engine.trt_precision,
        max_batch_size=settings.engine.trt_maximum_batch_size,
        max_seq_len=settings.session.maximum_sequence_length,
        kv_cache_config=KvCacheConfig(
            enable_block_reuse=True,
            free_gpu_memory_fraction=settings.gpu.gpu_memory_fraction,
            dtype=settings.gpu.key_value_cache_precision,
        ),
    )
    return TRTEngine(llm, SamplingParams, vocab_size)


__all__ = ["create_trt_engine"]
