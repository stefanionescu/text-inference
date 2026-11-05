#!/usr/bin/env bash
set -euo pipefail

SCRIPT_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=docker/base/scripts/logs.sh
source "/app/base/scripts/logs.sh"
# shellcheck source=docker/base/scripts/server.sh
source "/app/base/scripts/server.sh"

is_logging_enabled=0
case "$#" in
  0) ;;
  1)
    case "$1" in
      --logs) is_logging_enabled=1 ;;
      --help | -h)
        container_show_usage
        exit 0
        ;;
      *)
        container_show_usage >&2
        exit 2
        ;;
    esac
    ;;
  *)
    container_show_usage >&2
    exit 2
    ;;
esac
LOGS_ENABLED="${is_logging_enabled}"
export LOGS_ENABLED

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
