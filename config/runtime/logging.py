"""Application logging configuration values."""

APPLICATION_LOG_LEVEL = "INFO"
APPLICATION_LOG_FORMAT = (
    "%(levelname)s %(asctime)s name=%(name)s session_id=%(session_id)s "
    "request_id=%(request_id)s client_id=%(client_id)s message=%(message)s"
)
APPLICATION_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

STREAM_LABEL = "generation"

DEPENDENCY_LOGGER_NAMES = (
    "accelerate",
    "awq",
    "compressed_tensors",
    "cuda",
    "datasets",
    "flashinfer",
    "huggingface_hub",
    "llmcompressor",
    "modelopt",
    "py.warnings",
    "safetensors",
    "tensorrt_llm",
    "tokenizers",
    "torch",
    "torchvision",
    "transformers",
    "triton",
    "uvicorn",
    "vllm",
    "xformers",
)

DEPENDENCY_QUIET_ENVIRONMENT = {
    "HF_HUB_DISABLE_PROGRESS_BARS": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "TOKENIZERS_PARALLELISM": "false",
    "TRANSFORMERS_NO_ADVISORY_WARNINGS": "1",
    "TRANSFORMERS_VERBOSITY": "error",
    "TQDM_DISABLE": "1",
    "TRTLLM_LOG_LEVEL": "error",
    "VLLM_LOGGING_LEVEL": "ERROR",
}


__all__ = [
    "APPLICATION_LOG_DATE_FORMAT",
    "APPLICATION_LOG_FORMAT",
    "APPLICATION_LOG_LEVEL",
    "DEPENDENCY_LOGGER_NAMES",
    "DEPENDENCY_QUIET_ENVIRONMENT",
    "STREAM_LABEL",
]
