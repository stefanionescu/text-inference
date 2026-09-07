#!/usr/bin/env bash
#
# Validate and launch a detached host inference deployment.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly SCRIPT_DIR
ROOT_DIR="$(CDPATH='' cd -- "${SCRIPT_DIR}/.." && pwd -P)" || exit 1
readonly ROOT_DIR
export ROOT_DIR

# shellcheck source=scripts/config/defaults.sh
source "${SCRIPT_DIR}/config/defaults.sh"
# shellcheck source=scripts/config/messages/main.sh
source "${SCRIPT_DIR}/config/messages/main.sh"
# shellcheck source=scripts/config/values/deployment.sh
source "${SCRIPT_DIR}/config/values/deployment.sh"
# shellcheck source=scripts/lib/restart/engine.sh
source "${SCRIPT_DIR}/lib/restart/engine.sh"
# shellcheck source=scripts/lib/runtime/background.sh
source "${SCRIPT_DIR}/lib/runtime/background.sh"
# shellcheck source=scripts/lib/runtime/warmup/process.sh
source "${SCRIPT_DIR}/lib/runtime/warmup/process.sh"
# shellcheck source=scripts/lib/shared/deployment.sh
source "${SCRIPT_DIR}/lib/shared/deployment.sh"
# shellcheck source=scripts/lib/shared/inspection.sh
source "${SCRIPT_DIR}/lib/shared/inspection.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${SCRIPT_DIR}/lib/shared/log.sh"

# _main_usage - Print deployment command help and terminate.
_main_usage() {
  local status="$1"
  local line

  for line in "${CFG_MAIN_USAGE_LINES[@]}"; do
    printf '%s\n' "${line//\$0/$0}"
  done
  exit "${status}"
}

# _main_export_args - Export one validated deployment argument set.
_main_export_args() {
  INFERENCE_ENGINE="$1"
  LOGS_ENABLED="$2"
  PUSH_REQUESTED="$3"
  REQUESTED_QUANTIZATION="$4"
  SOURCE_MODEL="$5"
  MODEL="${SOURCE_MODEL}"
  export INFERENCE_ENGINE LOGS_ENABLED MODEL PUSH_REQUESTED
  export REQUESTED_QUANTIZATION SOURCE_MODEL
}

# _main_validate_args - Validate the named deployment arguments.
_main_validate_args() {
  local engine="$1"
  local model="$2"

  [[ ${engine} == "trt" || ${engine} == "vllm" ]] || return 2
  [[ -n ${model} ]]
}

# _main_parse_args - Parse the host deployment command contract.
_main_parse_args() {
  local engine="${CFG_DEFAULT_ENGINE}"
  local model=""
  local quantization=""
  local is_logging_enabled="0"
  local is_push_requested="0"

  while (($# > 0)); do
    case "$1" in
      --engine | --model | --quantization)
        (($# >= 2)) || return 2
        case "$1" in
          --engine) engine="$2" ;;
          --model) model="$2" ;;
          --quantization) quantization="$2" ;;
          *) return 2 ;;
        esac
        shift 2
        ;;
      --logs)
        is_logging_enabled=1
        shift
        ;;
      --push)
        is_push_requested=1
        shift
        ;;
      --help | -h) _main_usage 0 ;;
      --*)
        log_write "[main] Unknown flag: $1"
        return 2
        ;;
      *) return 2 ;;
    esac
  done
  _main_validate_args "${engine}" "${model}" || return 2
  _main_export_args \
    "${engine}" "${is_logging_enabled}" "${is_push_requested}" \
    "${quantization}" "${model}"
}

# main - Validate configuration and start the deployment pipeline.
main() {
  local transition

  log_write "[main] Starting Text Inference Server"
  _main_parse_args "$@" || _main_usage 2
  deployment_require_environment
  deployment_inspect_model \
    "${ROOT_DIR}" "${SOURCE_MODEL}" "${INFERENCE_ENGINE}" "${REQUESTED_QUANTIZATION}"
  transition="$(
    restart_transition_mode \
      "${ROOT_DIR}" "${INFERENCE_ENGINE}" "${SOURCE_MODEL}" \
      "${SOURCE_REVISION}" "${REQUESTED_QUANTIZATION}"
  )"
  warmup_stop_existing "${ROOT_DIR}"
  restart_apply_transition "${ROOT_DIR}" "${transition}"
  runtime_start_background \
    "${ROOT_DIR}" \
    "Starting ${INFERENCE_ENGINE} deployment" \
    bash "${SCRIPT_DIR}/deploy/main.sh"
}

main "$@"
