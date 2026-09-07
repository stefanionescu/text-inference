"""Quantization artifact and format policy."""

VLLM_ENGINE = "vllm"
TRT_ENGINE = "trt"
BINARY_FLAG_VALUES = ("0", "1")

AWQ_FORMAT = "awq"
COMPRESSED_TENSORS_FORMAT = "compressed-tensors"
FP8_FORMAT = "fp8"
GPTQ_FORMAT = "gptq"
INT4_AWQ_FORMAT = "int4_awq"
MODELOPT_METHOD = "modelopt"
NVFP4_FORMAT = "nvfp4"

# Detection retains historical ModelOpt algorithms so incompatible checkpoints can
# be identified precisely even when the active runtime does not support them.
MODELOPT_ALGORITHM_FORMATS = {
    "FP8": FP8_FORMAT,
    "NVFP4": NVFP4_FORMAT,
    "W4A16_AWQ": INT4_AWQ_FORMAT,
    "W4A16_NVFP4": NVFP4_FORMAT,
    "W8A8_SQ_PER_CHANNEL": "int8_sq",
}

MODEL_CONFIG_FILENAME = "config.json"
QUANTIZATION_CONFIG_FIELD = "quantization_config"
QUANTIZATION_METHOD_FIELDS = ("quant_method", "quantization_method")
MODELOPT_ALGORITHM_FIELD = "quant_algo"
QUANTIZATION_CONFIG_FILENAMES = (
    "config.json",
    "quantization_config.json",
    "quant_config.json",
    "awq_config.json",
)

DEFAULT_MODEL_REVISION = "main"
HUB_SOURCE_KIND = "hub"
HUB_COMMIT_PATTERN_TEXT = r"^[0-9a-f]{40}$"
LOCAL_SOURCE_KIND = "local"
SOURCE_FINGERPRINT_SUFFIXES = (".bin", ".json", ".model", ".py", ".safetensors")

CHECKPOINT_ASSET_FILENAMES = (
    "LICENSE",
    "added_tokens.json",
    "chat_template.jinja",
    "generation_config.json",
    "merges.txt",
    "preprocessor_config.json",
    "processor_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
    "vocab.json",
)

METADATA_FILENAME = "quantization_metadata.json"
METADATA_SCHEMA_VERSION = 1

QUANTIZATIONS_BY_ENGINE = {
    VLLM_ENGINE: (AWQ_FORMAT, GPTQ_FORMAT, COMPRESSED_TENSORS_FORMAT, FP8_FORMAT, NVFP4_FORMAT),
    TRT_ENGINE: (INT4_AWQ_FORMAT, NVFP4_FORMAT, FP8_FORMAT),
}

__all__ = [
    "AWQ_FORMAT",
    "BINARY_FLAG_VALUES",
    "CHECKPOINT_ASSET_FILENAMES",
    "COMPRESSED_TENSORS_FORMAT",
    "DEFAULT_MODEL_REVISION",
    "FP8_FORMAT",
    "GPTQ_FORMAT",
    "HUB_COMMIT_PATTERN_TEXT",
    "HUB_SOURCE_KIND",
    "INT4_AWQ_FORMAT",
    "LOCAL_SOURCE_KIND",
    "METADATA_FILENAME",
    "METADATA_SCHEMA_VERSION",
    "MODELOPT_ALGORITHM_FIELD",
    "MODELOPT_ALGORITHM_FORMATS",
    "MODELOPT_METHOD",
    "MODEL_CONFIG_FILENAME",
    "NVFP4_FORMAT",
    "QUANTIZATIONS_BY_ENGINE",
    "QUANTIZATION_CONFIG_FIELD",
    "QUANTIZATION_CONFIG_FILENAMES",
    "QUANTIZATION_METHOD_FIELDS",
    "SOURCE_FINGERPRINT_SUFFIXES",
    "TRT_ENGINE",
    "VLLM_ENGINE",
]
