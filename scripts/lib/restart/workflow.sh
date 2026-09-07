#!/usr/bin/env bash
#
# Coordinate process, dependency, model, and server restart operations.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the complete host restart orchestration workflow.

_RESTART_WORKFLOW_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/deploy/environment.sh
source "${_RESTART_WORKFLOW_DIR}/../../deploy/environment.sh"
# shellcheck source=scripts/lib/restart/dependencies.sh
source "${_RESTART_WORKFLOW_DIR}/dependencies.sh"
# shellcheck source=scripts/lib/restart/engine.sh
source "${_RESTART_WORKFLOW_DIR}/engine.sh"
# shellcheck source=scripts/lib/restart/model.sh
source "${_RESTART_WORKFLOW_DIR}/model.sh"
# shellcheck source=scripts/lib/restart/reset.sh
source "${_RESTART_WORKFLOW_DIR}/reset.sh"
# shellcheck source=scripts/lib/runtime/background.sh
source "${_RESTART_WORKFLOW_DIR}/../runtime/background.sh"
# shellcheck source=scripts/lib/runtime/warmup/process.sh
source "${_RESTART_WORKFLOW_DIR}/../runtime/warmup/process.sh"
# shellcheck source=scripts/lib/shared/deployment.sh
source "${_RESTART_WORKFLOW_DIR}/../shared/deployment.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_RESTART_WORKFLOW_DIR}/../shared/log.sh"
# shellcheck source=scripts/lib/shared/publishing.sh
source "${_RESTART_WORKFLOW_DIR}/../shared/publishing.sh"

# _restart_transition - Print the requested restart transition.
_restart_transition() {
  local root_dir="$1"

  if [[ ${RESET_HOST:?RESET_HOST is required} == "1" ]]; then
    printf 'reset\n'
    return 0
  fi
  restart_transition_mode \
    "${root_dir}" \
    "${INFERENCE_ENGINE:?INFERENCE_ENGINE is required}" \
    "${SOURCE_MODEL:?SOURCE_MODEL is required}" \
    "${SOURCE_REVISION:?SOURCE_REVISION is required}" \
    "${REQUESTED_QUANTIZATION-}"
}

# _restart_checkpoint_mode - Print whether checkpoint preparation is required.
_restart_checkpoint_mode() {
  case "$1" in
    same) printf 'reuse\n' ;;
    engine | fresh | model | reset) printf 'prepare\n' ;;
    *) return 2 ;;
  esac
}

# restart_execute_selected - Apply one inspected restart selection.
# Globals:
#   Inspected restart state and action flags.
# Arguments:
#   $1: Repository root. $2: Scripts directory.
# Outputs:
#   Writes restart progress to the captured deployment log.
# Returns:
#   0 after server startup and warmup, non-zero otherwise.
restart_execute_selected() {
  local root_dir="$1"
  local scripts_dir="$2"
  local transition="${RESTART_TRANSITION:?RESTART_TRANSITION is required}"
  local checkpoint_mode="${RESTART_CHECKPOINT_MODE:?RESTART_CHECKPOINT_MODE is required}"

  warmup_stop_existing "${root_dir}" || return 1
  if [[ ${RESTART_RESET_COMPLETED:?RESTART_RESET_COMPLETED is required} == "0" ]]; then
    restart_apply_transition "${root_dir}" "${transition}" || return 1
  fi
  export VENV_DIR="${root_dir}/${CFG_RUNTIME_VENV_DIR_REL}"
  export QUANT_VENV_DIR="${root_dir}/${CFG_QUANT_VENV_DIR_REL}"
  bash "${scripts_dir}/steps/01_check_gpu.sh" || return 1
  deploy_initialize_environment "${root_dir}" || return 1
  deployment_validate_cuda "restart" || return 1
  restart_prepare_dependencies "${scripts_dir}" "${transition}" || return 1
  deployment_validate_model || return 1
  publishing_validate || return 1
  restart_prepare_checkpoint "${checkpoint_mode}" || return 1
  bash "${scripts_dir}/steps/03_start_server.sh" || return 1
  log_write "[restart] Restart completed for ${INFERENCE_ENGINE}"
}

# restart_run - Inspect a restart request and start its captured workflow.
# Globals:
#   Restart flags and deployment environment variables.
# Arguments:
#   $1: Repository root. $2: Scripts directory.
# Outputs:
#   Writes restart progress and follows the deployment log.
# Returns:
#   The log follower status, or non-zero when inspection fails.
restart_run() {
  local root_dir="$1"
  local scripts_dir="$2"
  local transition
  local checkpoint_mode

  restart_select_model "${root_dir}" || return 1
  transition="$(_restart_transition "${root_dir}")" || return 1
  checkpoint_mode="$(_restart_checkpoint_mode "${transition}")" || return 1
  RESTART_RESET_COMPLETED=0
  if [[ ${transition} == "reset" ]]; then
    restart_capture_reset "${root_dir}" || return 1
    RESTART_RESET_COMPLETED=1
  fi
  RESTART_TRANSITION="${transition}"
  RESTART_CHECKPOINT_MODE="${checkpoint_mode}"
  export RESTART_CHECKPOINT_MODE RESTART_RESET_COMPLETED RESTART_TRANSITION
  runtime_start_background \
    "${root_dir}" \
    "Restarting ${INFERENCE_ENGINE} deployment" \
    bash "${scripts_dir}/deploy/restart.sh"
}
