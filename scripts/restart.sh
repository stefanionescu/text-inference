#!/usr/bin/env bash
#
# Restart an owned host server with persisted or new model settings.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly SCRIPT_DIR
ROOT_DIR="$(CDPATH='' cd -- "${SCRIPT_DIR}/.." && pwd -P)" || exit 1
readonly ROOT_DIR
export ROOT_DIR

# shellcheck source=scripts/config/defaults.sh
source "${SCRIPT_DIR}/config/defaults.sh"
# shellcheck source=scripts/config/messages/restart.sh
source "${SCRIPT_DIR}/config/messages/restart.sh"
# shellcheck source=scripts/lib/restart/workflow.sh
source "${SCRIPT_DIR}/lib/restart/workflow.sh"
# shellcheck source=scripts/lib/shared/deployment.sh
source "${SCRIPT_DIR}/lib/shared/deployment.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${SCRIPT_DIR}/lib/shared/log.sh"

# _restart_usage - Print restart command help and terminate.
_restart_usage() {
  local status="$1"
  local line

  for line in "${CFG_RESTART_USAGE_LINES[@]}"; do
    printf '%s\n' "${line}"
  done
  exit "${status}"
}

# _restart_export_model_args - Export parsed model selection arguments.
_restart_export_model_args() {
  INFERENCE_ENGINE="$1"
  MODEL_ARGUMENT="$2"
  QUANTIZATION_ARGUMENT="$3"
  MODEL_ARGUMENT_PROVIDED="$4"
  export INFERENCE_ENGINE MODEL_ARGUMENT MODEL_ARGUMENT_PROVIDED QUANTIZATION_ARGUMENT
}

# _restart_export_action_args - Export parsed restart action arguments.
_restart_export_action_args() {
  REINSTALL_REQUESTED="$1"
  RESET_HOST="$2"
  PUSH_REQUESTED="$3"
  LOGS_ENABLED="$4"
  export LOGS_ENABLED PUSH_REQUESTED REINSTALL_REQUESTED RESET_HOST
}

# _restart_parse_args - Parse the public restart command contract.
_restart_parse_args() {
  local engine="" model="" quantization="" is_model_provided="0"
  local is_reinstallation_requested="0" is_host_reset_requested="0" is_push_requested="0" is_logging_enabled="0"

  while (($# > 0)); do
    case "$1" in
      --engine | --model | --quantization)
        (($# >= 2)) || return 2
        case "$1" in
          --engine) engine="$2" ;;
          --model)
            model="$2"
            is_model_provided=1
            ;;
          --quantization)
            [[ -n $2 ]] || return 2
            quantization="$2"
            ;;
          *) return 2 ;;
        esac
        shift 2
        ;;
      --reinstall | --reset | --push | --logs)
        case "$1" in
          --reinstall) is_reinstallation_requested=1 ;;
          --reset) is_host_reset_requested=1 ;;
          --push) is_push_requested=1 ;;
          --logs) is_logging_enabled=1 ;;
          *) return 2 ;;
        esac
        shift
        ;;
      --help | -h) _restart_usage 0 ;;
      *) return 2 ;;
    esac
  done
  [[ -z ${engine} || ${engine} == "trt" || ${engine} == "vllm" ]] || return 2
  [[ ${is_model_provided} == "0" || -n ${model} ]] || return 2
  [[ -z ${quantization} || ${is_model_provided} == "1" ]] || return 2
  _restart_export_model_args "${engine}" "${model}" "${quantization}" "${is_model_provided}"
  _restart_export_action_args "${is_reinstallation_requested}" "${is_host_reset_requested}" \
    "${is_push_requested}" "${is_logging_enabled}"
}

# main - Validate restart inputs and execute the restart workflow.
main() {
  _restart_parse_args "$@" || _restart_usage 2
  deployment_require_environment
  log_write "[restart] Restarting Text Inference Server"
  restart_run "${ROOT_DIR}" "${SCRIPT_DIR}"
}

main "$@"
