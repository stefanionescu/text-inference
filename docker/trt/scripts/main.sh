#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=docker/shared/scripts/logs.sh
source "/app/shared/scripts/logs.sh"
# shellcheck source=docker/shared/scripts/server.sh
source "/app/shared/scripts/server.sh"

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

# shellcheck source=docker/trt/scripts/env.sh
source "${SCRIPT_DIR}/env.sh"
# shellcheck source=scripts/lib/shared/gpu/environment.sh
source "/app/scripts/lib/shared/gpu/environment.sh"
# shellcheck source=scripts/lib/env/trt.sh
source "/app/scripts/lib/env/trt.sh"
gpu_detect
gpu_apply_environment

: "${API_KEY:?API_KEY is required}"
RUNTIME_QUANTIZATION="$("${VENV_DIR:?VENV_DIR is required}/bin/python" \
  -m src.quantization.detection "${MODEL:?MODEL is required}")"
export RUNTIME_QUANTIZATION
if [[ -n ${RUNTIME_QUANTIZATION} ]]; then
  trt_validate_format "${RUNTIME_QUANTIZATION}" "${GPU_SM_ARCH}" || exit 1
fi
"${VENV_DIR}/bin/python" -m src.scripts.validate
CUDA_DEVICE_MAX_CONNECTIONS=2
export CUDA_DEVICE_MAX_CONNECTIONS
log_write "[trt] Model: ${MODEL}"
start_warmup_server "trt" "src.server.trt"
