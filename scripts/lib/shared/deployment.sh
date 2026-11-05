#!/usr/bin/env bash
#
# Validate shared host deployment inputs and publishing policy.
# Runtime: Bash 3.2+, Linux.

_DEPLOYMENT_SHARED_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/deployment.sh
source "${_DEPLOYMENT_SHARED_DIR}/../../config/values/deployment.sh"
# shellcheck source=scripts/config/patterns.sh
source "${_DEPLOYMENT_SHARED_DIR}/../../config/patterns.sh"
# shellcheck source=scripts/config/values/quantization.sh
source "${_DEPLOYMENT_SHARED_DIR}/../../config/values/quantization.sh"
# shellcheck source=scripts/engines/trt/detection.sh
source "${_DEPLOYMENT_SHARED_DIR}/../../engines/trt/detection.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_DEPLOYMENT_SHARED_DIR}/log.sh"

# deployment_require_environment: Validate required deployment environment values.
# Globals:
#   HF_TOKEN
#   MAX_CONCURRENT_CONNECTIONS
#   API_KEY
# Arguments:
#   None.
# Outputs:
#   Writes validation errors to standard error.
# Returns:
#   0 after exporting valid values, non-zero when a value is missing or invalid.
deployment_require_environment() {
  if [[ -z ${API_KEY-} ]]; then
    log_write "[env] API_KEY is required"
    return 1
  fi
  if [[ -z ${HF_TOKEN-} ]]; then
    log_write "[env] HF_TOKEN is required"
    return 1
  fi
  if [[ ! ${MAX_CONCURRENT_CONNECTIONS-} =~ ^[1-9][0-9]*$ ]]; then
    log_write "[env] MAX_CONCURRENT_CONNECTIONS must be a positive integer"
    return 1
  fi
  export HF_TOKEN MAX_CONCURRENT_CONNECTIONS API_KEY
}

# deployment_validate_model: Validate the configured model and quantization.
# Globals:
#   ROOT_DIR
#   VENV_DIR
# Arguments:
#   None.
# Outputs:
#   Writes validation output and failures to the caller streams.
# Returns:
#   0 for a valid deployment request, non-zero otherwise.
deployment_validate_model() {
  local python_bin="${VENV_DIR:?VENV_DIR is required}/bin/python"

  if [[ ! -x ${python_bin} ]]; then
    log_write "[validate] Managed Python is missing: ${python_bin}"
    return 1
  fi
  if ! PYTHONPATH="${ROOT_DIR:?ROOT_DIR is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.scripts.validate; then
    log_write "[validate] Model validation failed"
    return 1
  fi
}

# deployment_validate_cuda: Validate CUDA for the selected engine.
# Globals:
#   CFG_ENGINE_TRT
#   CFG_ENGINE_VLLM
#   INFERENCE_ENGINE
# Arguments:
#   $1: Diagnostic phase name.
# Outputs:
#   Writes validation failures to standard error.
# Returns:
#   0 for a supported runtime, non-zero otherwise.
deployment_validate_cuda() {
  local phase="$1"

  case "${INFERENCE_ENGINE:?INFERENCE_ENGINE is required}" in
    "${CFG_ENGINE_TRT}")
      trt_validate_cuda "${phase}"
      ;;
    "${CFG_ENGINE_VLLM}")
      return 0
      ;;
    *)
      log_write "[${phase}] Unsupported inference engine: ${INFERENCE_ENGINE}"
      return 1
      ;;
  esac
}
