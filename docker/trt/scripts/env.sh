#!/usr/bin/env bash
# TensorRT-LLM public PyTorch backend configuration.

# shellcheck source=scripts/config/defaults.sh
source "/app/scripts/config/defaults.sh"

cfg_export_default MAXIMUM_OUTPUT_TOKENS "150"
# Runtime settings aligned with config/model/trt.py.
cfg_export_default TRT_MAX_BATCH_SIZE "64"
cfg_export_default TRT_DTYPE "auto"
