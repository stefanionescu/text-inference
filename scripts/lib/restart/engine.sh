#!/usr/bin/env bash
#
# Select and apply cleanup for engine, model, and quantization transitions.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns persisted deployment transition cleanup policy.

_RESTART_ENGINE_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/lib/runtime/cleanup/artifacts.sh
source "${_RESTART_ENGINE_DIR}/../runtime/cleanup/artifacts.sh"
# shellcheck source=scripts/lib/runtime/cleanup/main.sh
source "${_RESTART_ENGINE_DIR}/../runtime/cleanup/main.sh"
# shellcheck source=scripts/lib/runtime/cleanup/reset.sh
source "${_RESTART_ENGINE_DIR}/../runtime/cleanup/reset.sh"
# shellcheck source=scripts/lib/runtime/records.sh
source "${_RESTART_ENGINE_DIR}/../runtime/records.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_RESTART_ENGINE_DIR}/../shared/log.sh"

# restart_transition_mode - Print cleanup mode for one requested deployment.
# Globals:
#   None.
# Arguments:
#   $1: Root. $2: Engine. $3: Source model. $4: Source revision.
#   $5: Requested quantization.
# Outputs:
#   Writes fresh, same, model, or engine to standard output.
# Returns:
#   0 for valid state, non-zero for malformed state.
restart_transition_mode() {
  local root_dir="$1"
  local requested_engine="$2"
  local requested_source="$3"
  local requested_revision="$4"
  local requested_quantization="$5"
  local previous_engine
  local previous_source
  local previous_revision
  local previous_request

  previous_engine="$(runtime_state_read "${root_dir}" INFERENCE_ENGINE)" || return 1
  previous_source="$(runtime_state_read "${root_dir}" SOURCE_MODEL)" || return 1
  previous_revision="$(runtime_state_read "${root_dir}" SOURCE_REVISION)" || return 1
  previous_request="$(runtime_state_read "${root_dir}" REQUESTED_QUANTIZATION)" || return 1
  if [[ -z ${previous_engine}${previous_source}${previous_revision}${previous_request} ]]; then
    printf 'fresh\n'
    return 0
  fi
  if [[ -z ${previous_engine} || -z ${previous_source} || -z ${previous_revision} ]]; then
    log_write "[restart] Persisted runtime state is incomplete"
    return 1
  fi
  if [[ ${previous_engine} != "${requested_engine}" ]]; then
    printf 'engine\n'
  elif [[ ${previous_source} != "${requested_source}" ||
    ${previous_revision} != "${requested_revision}" ||
    ${previous_request} != "${requested_quantization}" ]]; then
    printf 'model\n'
  else
    printf 'same\n'
  fi
}

# restart_apply_transition - Stop processes and invalidate changed artifacts.
# Globals:
#   None.
# Arguments:
#   $1: Repository root. $2: Transition mode.
# Outputs:
#   Writes selected cleanup progress to standard error.
# Returns:
#   0 after cleanup, non-zero when cleanup fails.
restart_apply_transition() {
  local root_dir="$1"
  local transition="$2"

  case "${transition}" in
    fresh | same)
      log_write "[restart] Stopping repository-owned processes"
      runtime_stop_owned_processes "${root_dir}"
      ;;
    model)
      log_write "[restart] Model or quantization changed; clearing model and engine caches"
      runtime_stop_owned_processes "${root_dir}" || return 1
      runtime_clear_model_transition "${root_dir}"
      ;;
    engine)
      log_write "[restart] Engine changed; clearing incompatible environments and caches"
      runtime_stop_owned_processes "${root_dir}" || return 1
      runtime_clear_engine_artifacts "${root_dir}"
      ;;
    reset)
      runtime_reset_host "${root_dir}"
      ;;
    *)
      log_write "[restart] Invalid deployment transition: ${transition}"
      return 2
      ;;
  esac
}
