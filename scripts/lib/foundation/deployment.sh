#!/usr/bin/env bash
#
# Validate shared host deployment inputs and publishing policy.
# Runtime: Bash 3.2+, Linux.

_DEPLOYMENT_FOUNDATION_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/deployment.sh
source "${_DEPLOYMENT_FOUNDATION_FOLDER}/../../config/values/deployment.sh"
# shellcheck source=scripts/config/patterns.sh
source "${_DEPLOYMENT_FOUNDATION_FOLDER}/../../config/patterns.sh"
# shellcheck source=scripts/config/values/quantization.sh
source "${_DEPLOYMENT_FOUNDATION_FOLDER}/../../config/values/quantization.sh"
# shellcheck source=scripts/engines/trt/detection.sh
source "${_DEPLOYMENT_FOUNDATION_FOLDER}/../../engines/trt/detection.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_DEPLOYMENT_FOUNDATION_FOLDER}/log.sh"

# deployment_require_environment - Validate required deployment environment values.
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

# deployment_validate_model - Validate the configured model and quantization.
# Globals:
#   ROOT_FOLDER
#   VENV_FOLDER
# Arguments:
#   None.
# Outputs:
#   Writes validation output and failures to the caller streams.
# Returns:
#   0 for a valid deployment request, non-zero otherwise.
deployment_validate_model() {
  local python_bin="${VENV_FOLDER:?VENV_FOLDER is required}/bin/python"

  if [[ ! -x ${python_bin} ]]; then
    log_write "[validate] Managed Python is missing: ${python_bin}"
    return 1
  fi
  if ! PYTHONPATH="${ROOT_FOLDER:?ROOT_FOLDER is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.scripts.validate; then
    log_write "[validate] Model validation failed"
    return 1
  fi
}

# deployment_validate_cuda - Validate CUDA for the selected engine.
# Globals:
#   ENGINE_TRT
#   ENGINE_VLLM
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
    "${ENGINE_TRT}")
      trt_validate_cuda "${phase}"
      ;;
    "${ENGINE_VLLM}")
      return 0
      ;;
    *)
      log_write "[${phase}] Unsupported inference engine: ${INFERENCE_ENGINE}"
      return 1
      ;;
  esac
}
