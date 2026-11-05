"""Hugging Face publishing and model-card policy."""

HUGGING_FACE_MODEL_URL = "https://huggingface.co/{model_name}/tree/{source_revision}"
DEFAULT_LICENSE = "other"
LOCAL_LICENSE_PATH = "LICENSE"

LICENSE_ID_FIELD = "license"
LICENSE_NAME_FIELD = "license_name"
LICENSE_LINK_FIELD = "license_link"

MODEL_CARD_TEMPLATE_FOLDER = "templates"
TRT_MODEL_CARD_TEMPLATE = "trt.md"
VLLM_MODEL_CARD_TEMPLATE = "vllm.md"
MODEL_CARD_FILENAME = "README.md"
MODEL_CARD_JSON_INDENT = 2
EMPTY_METADATA_ITEMS = "none"

HF_MODEL_REPO_TYPE = "model"
HF_DEFAULT_REVISION = "main"
TRT_UPLOAD_MESSAGE = "Upload {quantization_format} ModelOpt checkpoint"
VLLM_UPLOAD_MESSAGE = "Upload LLM Compressor 0.12 compressed-tensors checkpoint"

TRT_HF_IGNORE_PATTERNS = (".git/**", ".hf_staging/**", "*.tmp", "*.log", "__pycache__/*")
VLLM_HF_IGNORE_PATTERNS = (
    "*.tmp",
    "*.log",
    "__pycache__/*",
    "training_args.bin",
    "optimizer.pt",
    "scheduler.pt",
    "rng_state.pth",
)

TRT_FORMAT_LABELS = {
    "fp8": "FP8",
    "int4_awq": "INT4-AWQ",
    "nvfp4": "NVFP4",
}

TRT_WEIGHT_PRECISIONS = {
    "fp8": "8-bit floating point",
    "int4_awq": "4-bit integer",
    "nvfp4": "4-bit floating point",
}

TRT_GPU_REQUIREMENTS = {
    "fp8": "NVIDIA Ada or Hopper GPU supported by TensorRT-LLM",
    "int4_awq": "NVIDIA Ampere, Ada, Hopper, or Blackwell GPU supported by TensorRT-LLM",
    "nvfp4": "NVIDIA Blackwell GPU supported by TensorRT-LLM",
}

ENABLED_LABEL = "enabled"
DISABLED_LABEL = "disabled"
ALL_EXPERTS_LABEL = "all experts"
NOT_APPLICABLE_LABEL = "not applicable"
PYTHON_RUNTIME_VERSION = "3.12"

__all__ = [
    "ALL_EXPERTS_LABEL",
    "DEFAULT_LICENSE",
    "DISABLED_LABEL",
    "EMPTY_METADATA_ITEMS",
    "ENABLED_LABEL",
    "HF_DEFAULT_REVISION",
    "HF_MODEL_REPO_TYPE",
    "HUGGING_FACE_MODEL_URL",
    "LICENSE_ID_FIELD",
    "LICENSE_LINK_FIELD",
    "LICENSE_NAME_FIELD",
    "LOCAL_LICENSE_PATH",
    "MODEL_CARD_FILENAME",
    "MODEL_CARD_JSON_INDENT",
    "MODEL_CARD_TEMPLATE_FOLDER",
    "NOT_APPLICABLE_LABEL",
    "PYTHON_RUNTIME_VERSION",
    "TRT_FORMAT_LABELS",
    "TRT_GPU_REQUIREMENTS",
    "TRT_HF_IGNORE_PATTERNS",
    "TRT_MODEL_CARD_TEMPLATE",
    "TRT_UPLOAD_MESSAGE",
    "TRT_WEIGHT_PRECISIONS",
    "VLLM_HF_IGNORE_PATTERNS",
    "VLLM_MODEL_CARD_TEMPLATE",
    "VLLM_UPLOAD_MESSAGE",
]
