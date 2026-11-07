#!/usr/bin/env bash
#
# Validate or rebuild managed dependencies for a restart.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns restart-time virtual environment replacement and repair.

_RESTART_DEPENDENCIES_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/lib/deps/venv.sh
source "${_RESTART_DEPENDENCIES_FOLDER}/../deps/venv.sh"
# shellcheck source=scripts/lib/runtime/cleanup/paths.sh
source "${_RESTART_DEPENDENCIES_FOLDER}/../runtime/cleanup/paths.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_RESTART_DEPENDENCIES_FOLDER}/../foundation/log.sh"
# shellcheck source=scripts/lib/foundation/pytorch_guard.sh
source "${_RESTART_DEPENDENCIES_FOLDER}/../foundation/pytorch_guard.sh"

# _restart_rebuild_dependencies - Replace both managed environments.
_restart_rebuild_dependencies() {
  local scripts_folder="$1"

  log_write "[restart] Rebuilding managed Python environments"
  runtime_remove_owned_path \
    "${ROOT_FOLDER:?ROOT_FOLDER is required}" "${VENV_FOLDER:?VENV_FOLDER is required}" || return 1
  runtime_remove_owned_path \
    "${ROOT_FOLDER}" "${QUANT_VENV_FOLDER:?QUANT_VENV_FOLDER is required}" || return 1
  venv_prepare "${VENV_FOLDER}" || return 1
  bash "${scripts_folder}/steps/install_deps.sh"
}

# _restart_torch_status - Return the managed environment compatibility status.
_restart_torch_status() {
  if [[ ! -x ${VENV_FOLDER:?VENV_FOLDER is required}/bin/python ]]; then
    return 0
  fi
  pytorch_guard_check "[restart]"
}

# _restart_apply_transition - Request a rebuild for the transitions that need one.
_restart_apply_transition() {
  case "$1" in
    engine | reset)
      REINSTALL_REQUESTED=1
      export REINSTALL_REQUESTED
      ;;
    fresh | model | same) ;;
    *) return 2 ;;
  esac
}

# restart_prepare_dependencies - Rebuild dependencies when requested or required.
# Globals:
#   REINSTALL_REQUESTED, ROOT_FOLDER, QUANT_VENV_FOLDER, VENV_FOLDER.
# Arguments:
#   $1: Scripts directory. $2: Deployment transition.
# Outputs:
#   Writes dependency and repair progress to standard error.
# Returns:
#   0 for a compatible environment, non-zero otherwise.
restart_prepare_dependencies() {
  local scripts_folder="$1"
  local transition="$2"
  local torch_status=0

  _restart_apply_transition "${transition}" || return 2
  _restart_torch_status || torch_status=$?
  if ((torch_status == 42)); then
    log_write "[restart] Torch mismatch requires a clean dependency rebuild"
    REINSTALL_REQUESTED=1
    export REINSTALL_REQUESTED
  elif ((torch_status != 0)); then
    return "${torch_status}"
  fi
  if [[ ! -x ${VENV_FOLDER}/bin/python ]]; then
    log_write "[restart] Managed environment is missing; rebuilding automatically"
    REINSTALL_REQUESTED=1
    export REINSTALL_REQUESTED
  fi
  if [[ ${REINSTALL_REQUESTED:?REINSTALL_REQUESTED is required} == "1" ]]; then
    _restart_rebuild_dependencies "${scripts_folder}" || return 1
  fi
  torch_status=0
  pytorch_guard_check "[restart]" || torch_status=$?
  if ((torch_status != 0)); then
    if ((torch_status == 42)); then
      log_write "[restart] Dependency rebuild did not repair the Torch mismatch"
    fi
    return "${torch_status}"
  fi
}
