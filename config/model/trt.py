"""TensorRT-LLM runtime and ModelOpt metadata."""

TRT_MAX_BATCH_SIZE = 64
TRT_DTYPE = "auto"
TRT_MODEL_DTYPES: set[str] = {"auto", "bfloat16", "float16", "float32"}
TRT_VERSION = "1.3.0rc20"
MODELOPT_QUANTIZER_NAME = "NVIDIA Model Optimizer"
MODELOPT_CALIBRATION_BATCH_SIZE = "automatic"

__all__ = [
    "MODELOPT_CALIBRATION_BATCH_SIZE",
    "MODELOPT_QUANTIZER_NAME",
    "TRT_DTYPE",
    "TRT_MAX_BATCH_SIZE",
    "TRT_MODEL_DTYPES",
    "TRT_VERSION",
]
