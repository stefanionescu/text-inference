#!/usr/bin/env bash
#
# Perform the explicit dedicated-host process, GPU, and cache reset.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns opt-in destructive reset of inference host resources.

_RUNTIME_RESET_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1
# shellcheck source=scripts/lib/runtime/cleanup/artifacts.sh
source "${_RUNTIME_RESET_DIR}/artifacts.sh"
# shellcheck source=scripts/lib/runtime/cleanup/host.sh
source "${_RUNTIME_RESET_DIR}/host.sh"
# shellcheck source=scripts/lib/runtime/cleanup/main.sh
source "${_RUNTIME_RESET_DIR}/main.sh"
# shellcheck source=scripts/lib/runtime/cleanup/python.sh
source "${_RUNTIME_RESET_DIR}/python.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_RUNTIME_RESET_DIR}/../../shared/log.sh"
# _runtime_reset_kill_pattern - Signal all helpers matching one reset pattern.
_runtime_reset_kill_pattern() {
  local signal_name="$1"
  local pattern="$2"
  local status

  if pkill "-${signal_name}" -f "${pattern}" 2>/dev/null; then
    return 0
  else
    status=$?
  fi
  if ((status == 1)); then
    return 0
  fi
  log_write "[reset] pkill failed for pattern '${pattern}' with status ${status}"
  return "${status}"
}
# _runtime_reset_engine_helpers - Terminate broad inference helper matches.
_runtime_reset_engine_helpers() {
  local pattern
  local status=0
  local -a patterns=(
    "vllm.v1.engine.core" "EngineCore_0" "python.*vllm"
    "python.*tensorrt" "python.*trtllm" "trtllm-build"
    "quantize.py" "mpirun" "mpi4py" "python.*cuda"
  )

  for pattern in "${patterns[@]}"; do
    _runtime_reset_kill_pattern TERM "${pattern}" || status=1
  done
  sleep 1
  for pattern in "${patterns[@]}"; do
    _runtime_reset_kill_pattern KILL "${pattern}" || status=1
  done
  return "${status}"
}

# _runtime_reset_gpu_pids - Terminate every detected GPU compute PID.
# Globals:
#   None.
# Arguments:
#   GPU process identifiers.
# Outputs:
#   Writes termination failures to standard error.
# Returns:
#   0 when no selected process remains, non-zero otherwise.
_runtime_reset_gpu_pids() {
  local pid
  local status=0

  for pid in "$@"; do
    if ! kill -TERM "${pid}" 2>/dev/null && kill -0 "${pid}" 2>/dev/null; then
      log_write "[reset] Failed to terminate GPU process ${pid}"
      status=1
    fi
  done
  (($# == 0)) || sleep 2
  for pid in "$@"; do
    if kill -0 "${pid}" 2>/dev/null &&
      ! kill -KILL "${pid}" 2>/dev/null; then
      log_write "[reset] Failed to kill GPU process ${pid}"
      status=1
    fi
  done
  return "${status}"
}

# _runtime_reset_gpu - Terminate GPU users and reset the hardware.
_runtime_reset_gpu() {
  local output
  local pid
  local status=0
  local -a pids=()

  command -v nvidia-smi >/dev/null 2>&1 || {
    log_write "[reset] nvidia-smi is required for --reset"
    return 1
  }
  output="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" || {
    log_write "[reset] Failed to query GPU compute processes"
    return 1
  }
  while IFS= read -r pid; do
    pid="${pid//[[:space:]]/}"
    [[ ${pid} =~ ^[1-9][0-9]*$ ]] && pids+=("${pid}")
  done <<<"${output}"
  _runtime_reset_gpu_pids "${pids[@]}" || status=1
  if ! nvidia-smi --gpu-reset; then
    log_write "[reset] GPU reset failed"
    status=1
  fi
  return "${status}"
}

# runtime_reset_host - Perform every explicit reset operation and report failures.
# Globals:
#   None.
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes reset progress and failures to standard error.
# Returns:
#   0 when every reset stage succeeds, non-zero otherwise.
runtime_reset_host() {
  local root_dir="$1"
  local status=0

  log_write "[reset] Stopping repository-owned process groups"
  runtime_stop_owned_processes "${root_dir}" || status=1
  log_write "[reset] Terminating inference engine helpers"
  _runtime_reset_engine_helpers || status=1
  log_write "[reset] Terminating GPU processes and resetting the GPU"
  _runtime_reset_gpu || status=1
  log_write "[reset] Removing repository deployment artifacts"
  runtime_clear_reset_artifacts "${root_dir}" || status=1
  log_write "[reset] Removing host inference and package caches"
  runtime_reset_host_caches || status=1
  runtime_cleanup_python_artifacts "${root_dir}" || status=1
  if ((status != 0)); then
    log_write "[reset] Reset completed with failures"
  fi
  return "${status}"
}
