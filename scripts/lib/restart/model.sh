#!/usr/bin/env bash
#
# Resolve persisted or newly requested restart model configuration.
# Runtime: Bash 3.2+, Linux.
_RESTART_MODEL_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=scripts/config/defaults.sh
source "${_RESTART_MODEL_FOLDER}/../../config/defaults.sh"
# shellcheck source=scripts/config/values/deployment.sh
source "${_RESTART_MODEL_FOLDER}/../../config/values/deployment.sh"
# shellcheck source=scripts/engines/trt/main.sh
source "${_RESTART_MODEL_FOLDER}/../../engines/trt/main.sh"
# shellcheck source=scripts/engines/trt/publishing.sh
source "${_RESTART_MODEL_FOLDER}/../../engines/trt/publishing.sh"
# shellcheck source=scripts/engines/vllm.sh
source "${_RESTART_MODEL_FOLDER}/../../engines/vllm.sh"
# shellcheck source=scripts/lib/runtime/records.sh
source "${_RESTART_MODEL_FOLDER}/../runtime/records.sh"
# shellcheck source=scripts/lib/foundation/deployment.sh
source "${_RESTART_MODEL_FOLDER}/../foundation/deployment.sh"
# shellcheck source=scripts/lib/foundation/inspection.sh
source "${_RESTART_MODEL_FOLDER}/../foundation/inspection.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_RESTART_MODEL_FOLDER}/../foundation/log.sh"

# _restart_read_persisted - Read the complete persisted deployment identity.
_restart_read_persisted() {
  local root_folder="$1"

  PERSISTED_ENGINE="$(runtime_state_read "${root_folder}" INFERENCE_ENGINE)" || return 1
  SOURCE_MODEL="$(runtime_state_read "${root_folder}" SOURCE_MODEL)" || return 1
  SOURCE_REVISION="$(runtime_state_read "${root_folder}" SOURCE_REVISION)" || return 1
  RESOLVED_CHECKPOINT="$(runtime_state_read "${root_folder}" RESOLVED_CHECKPOINT)" || return 1
  RUNTIME_QUANTIZATION="$(runtime_state_read "${root_folder}" RUNTIME_QUANTIZATION)" || return 1
  REQUESTED_QUANTIZATION="$(runtime_state_read "${root_folder}" REQUESTED_QUANTIZATION)" || return 1
  EXPORT_PROVENANCE="$(runtime_state_read "${root_folder}" EXPORT_PROVENANCE)" || return 1
  [[ -n ${PERSISTED_ENGINE} && -n ${SOURCE_MODEL} && -n ${SOURCE_REVISION} &&
    -n ${RESOLVED_CHECKPOINT} ]] || {
    log_write "[restart] No complete persisted deployment is available"
    return 1
  }
}

# _restart_select_requested - Inspect a newly supplied model configuration.
_restart_select_requested() {
  local root_folder="$1"
  local requested_engine="$2"
  local model_argument="$3"
  local quantization_argument="$4"

  if [[ -z ${requested_engine} ]]; then
    PERSISTED_ENGINE="$(runtime_state_read "${root_folder}" INFERENCE_ENGINE)" || return 1
    config_set_default PERSISTED_ENGINE "${DEFAULT_ENGINE}"
    requested_engine="${PERSISTED_ENGINE}"
  fi
  INFERENCE_ENGINE="${requested_engine}"
  deployment_inspect_model \
    "${root_folder}" "${model_argument}" "${INFERENCE_ENGINE}" "${quantization_argument}" || return 1
  RESOLVED_CHECKPOINT=""
  EXPORT_PROVENANCE=""
}

# _restart_select_persisted - Reuse or re-inspect persisted model state.
_restart_select_persisted() {
  local root_folder="$1"
  local requested_engine="$2"

  _restart_read_persisted "${root_folder}" || return 1
  config_set_default requested_engine "${PERSISTED_ENGINE}"
  INFERENCE_ENGINE="${requested_engine}"
  if [[ ${INFERENCE_ENGINE} != "${PERSISTED_ENGINE}" || ${RESET_HOST:?RESET_HOST is required} == "1" ]]; then
    MODEL_REVISION="${SOURCE_REVISION}" deployment_inspect_model \
      "${root_folder}" "${SOURCE_MODEL}" "${INFERENCE_ENGINE}" "${REQUESTED_QUANTIZATION}" || return 1
    RESOLVED_CHECKPOINT=""
    EXPORT_PROVENANCE=""
  else
    CHECKPOINT_ACTION="reuse"
    MODEL="${RESOLVED_CHECKPOINT}"
  fi
}

# restart_select_model - Resolve and inspect new or transition-sensitive inputs.
# Globals:
#   Restart model arguments and persisted deployment fields.
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes inspection diagnostics to standard error.
# Returns:
#   0 for a complete selected model, non-zero otherwise.
restart_select_model() {
  local root_folder="$1"
  local requested_engine="${INFERENCE_ENGINE-}"
  local model_argument="${MODEL_ARGUMENT-}"
  local quantization_argument="${QUANTIZATION_ARGUMENT-}"

  if [[ ${MODEL_ARGUMENT_PROVIDED:?MODEL_ARGUMENT_PROVIDED is required} == "1" ]]; then
    _restart_select_requested \
      "${root_folder}" "${requested_engine}" "${model_argument}" "${quantization_argument}" || return 1
  else
    _restart_select_persisted "${root_folder}" "${requested_engine}" || return 1
  fi
  export CHECKPOINT_ACTION EXPORT_PROVENANCE INFERENCE_ENGINE MODEL
  export REQUESTED_QUANTIZATION RESOLVED_CHECKPOINT RUNTIME_QUANTIZATION
  export SOURCE_MODEL SOURCE_REVISION
}

# restart_prepare_checkpoint - Prepare a checkpoint or publish a validated reuse.
# Globals:
#   Active engine, checkpoint, quantization, provenance, and publishing state.
# Arguments:
#   $1: reuse or prepare checkpoint mode.
# Outputs:
#   Writes publishing or checkpoint preparation output to the caller streams.
# Returns:
#   0 for a prepared or reused checkpoint, non-zero otherwise.
restart_prepare_checkpoint() {
  local checkpoint_mode="$1"

  if [[ ${checkpoint_mode} == "reuse" ]]; then
    if [[ ${PUSH_REQUESTED:?PUSH_REQUESTED is required} == "0" ]]; then
      return 0
    fi
    [[ -n ${EXPORT_PROVENANCE-} && ${EXPORT_PROVENANCE} == "${RESOLVED_CHECKPOINT}" ]] || {
      log_write "[restart] --push requires a persisted repository-provenanced local export"
      return 1
    }
    case "${INFERENCE_ENGINE}" in
      trt) trt_publish_checkpoint "${EXPORT_PROVENANCE}" "${RUNTIME_QUANTIZATION}" ;;
      vllm) vllm_publish_checkpoint "${EXPORT_PROVENANCE}" ;;
      *) return 2 ;;
    esac
    return
  fi
  [[ ${checkpoint_mode} == "prepare" ]] || return 2
  case "${INFERENCE_ENGINE}" in
    trt) trt_prepare_checkpoint ;;
    vllm) vllm_prepare_checkpoint ;;
    *) return 2 ;;
  esac
}
