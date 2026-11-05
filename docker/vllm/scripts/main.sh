#!/usr/bin/env bash
set -euo pipefail

SCRIPT_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=docker/base/scripts/server.sh
source "/app/base/scripts/server.sh"
container_read_arguments "$@"

# shellcheck source=docker/vllm/scripts/gpu.sh
source "${SCRIPT_FOLDER}/gpu.sh"
vllm_configure_gpu
: "${API_KEY:?API_KEY is required}"
RUNTIME_QUANTIZATION="$("${VENV_FOLDER:?VENV_FOLDER is required}/bin/python" \
  -m src.quantization.detection "${MODEL:?MODEL is required}")"
export RUNTIME_QUANTIZATION
"${VENV_FOLDER}/bin/python" -m src.scripts.validate
log_write "[vllm] GPU: ${DETECTED_GPU_NAME:?DETECTED_GPU_NAME is required}"
log_write "[vllm] Model: ${MODEL}"
start_warmup_server "vllm" "src.server.vllm"
