#!/usr/bin/env bash
set -euo pipefail

SCRIPT_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=docker/base/scripts/server.sh
source "/app/base/scripts/server.sh"
container_read_arguments "$@"

# shellcheck source=docker/trt/scripts/env.sh
source "${SCRIPT_FOLDER}/env.sh"
trt_export_defaults
# shellcheck source=scripts/lib/foundation/gpu/environment.sh
source "/app/scripts/lib/foundation/gpu/environment.sh"
# shellcheck source=scripts/lib/env/trt.sh
source "/app/scripts/lib/env/trt.sh"
gpu_detect
gpu_apply_environment

: "${API_KEY:?API_KEY is required}"
RUNTIME_QUANTIZATION="$("${VENV_FOLDER:?VENV_FOLDER is required}/bin/python" \
  -m src.quantization.detection "${MODEL:?MODEL is required}")"
export RUNTIME_QUANTIZATION
if [[ -n ${RUNTIME_QUANTIZATION} ]]; then
  trt_validate_format "${RUNTIME_QUANTIZATION}" "${GPU_SM_ARCH}" || exit 1
fi
"${VENV_FOLDER}/bin/python" -m src.scripts.validate
CUDA_DEVICE_MAX_CONNECTIONS=2
export CUDA_DEVICE_MAX_CONNECTIONS
log_write "[trt] Model: ${MODEL}"
start_warmup_server "trt" "src.server.trt"
