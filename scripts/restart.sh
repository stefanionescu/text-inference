#!/usr/bin/env bash
#
# Restart an owned host server with persisted or new model settings.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

# shellcheck source=scripts/lib/foundation/folders.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/foundation/folders.sh"
# shellcheck source=scripts/config/defaults.sh
source "${SCRIPTS_FOLDER}/config/defaults.sh"
# shellcheck source=scripts/config/messages/restart.sh
source "${SCRIPTS_FOLDER}/config/messages/restart.sh"
# shellcheck source=scripts/lib/restart/workflow.sh
source "${SCRIPTS_FOLDER}/lib/restart/workflow.sh"
# shellcheck source=scripts/lib/foundation/deployment.sh
source "${SCRIPTS_FOLDER}/lib/foundation/deployment.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${SCRIPTS_FOLDER}/lib/foundation/log.sh"

# _restart_usage - Print restart command help and terminate.
_restart_usage() {
  local status="$1"
  local line

  for line in "${RESTART_USAGE_LINES[@]}"; do
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

# _restart_read_value_flag - Store one flag's value in the variables of _restart_parse_args.
_restart_read_value_flag() {
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
}

# _restart_read_action_flag - Record one switch in the variables of _restart_parse_args.
_restart_read_action_flag() {
  case "$1" in
    --reinstall) is_reinstallation_requested=1 ;;
    --reset) is_host_reset_requested=1 ;;
    --push) is_push_requested=1 ;;
    --logs) is_logging_enabled=1 ;;
    *) return 2 ;;
  esac
}

# _restart_parse_args - Parse the public restart command contract.
_restart_parse_args() {
  local engine="" model="" quantization="" is_model_provided="0"
  local is_reinstallation_requested="0" is_host_reset_requested="0" is_push_requested="0" is_logging_enabled="0"

  while (($# > 0)); do
    case "$1" in
      --engine | --model | --quantization)
        (($# >= 2)) || return 2
        _restart_read_value_flag "$1" "$2" || return 2
        shift 2
        ;;
      --reinstall | --reset | --push | --logs)
        _restart_read_action_flag "$1" || return 2
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
  restart_run "${ROOT_FOLDER}" "${SCRIPTS_FOLDER}"
}

main "$@"
