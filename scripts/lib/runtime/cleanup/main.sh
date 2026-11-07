#!/usr/bin/env bash
#
# Stop process groups recorded by repository-owned PID files.
# Runtime: Bash 3.2+, macOS and Linux.
# Boundary: Owns termination of repository-recorded process groups.

_RUNTIME_CLEANUP_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/runtime.sh
source "${_RUNTIME_CLEANUP_FOLDER}/../../../config/values/runtime.sh"
# shellcheck source=scripts/lib/runtime/process.sh
source "${_RUNTIME_CLEANUP_FOLDER}/../process.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_RUNTIME_CLEANUP_FOLDER}/../../foundation/log.sh"

# _runtime_cleanup_wait - Wait briefly for an owned process to stop.
# Globals:
#   None.
# Arguments:
#   $1: Process identifier.
# Outputs:
#   None.
# Returns:
#   0 after exit, non-zero after the bounded wait.
_runtime_cleanup_wait() {
  local pid="$1"
  local attempt

  for ((attempt = 0; attempt < 10; attempt++)); do
    if ! kill -0 "${pid}" 2>/dev/null; then
      return 0
    fi
    sleep 1
  done
  return 1
}

# _runtime_cleanup_process - Stop the process group recorded in one PID file.
# Globals:
#   None.
# Arguments:
#   $1: Repository-owned PID file.
# Outputs:
#   Writes termination failures to standard error.
# Returns:
#   0 when no process remains, non-zero otherwise.
_runtime_cleanup_process() {
  local pid_file="$1"
  local pid

  if ! pid="$(runtime_read_pid "${pid_file}")"; then
    rm -f -- "${pid_file}"
    return 0
  fi
  if ! kill -0 "${pid}" 2>/dev/null; then
    rm -f -- "${pid_file}"
    return 0
  fi
  if ! kill -TERM "-${pid}" 2>/dev/null && kill -0 "${pid}" 2>/dev/null; then
    log_write "[stop] Failed to terminate owned process group ${pid}"
    return 1
  fi
  if ! _runtime_cleanup_wait "${pid}"; then
    if ! kill -KILL "-${pid}" 2>/dev/null && kill -0 "${pid}" 2>/dev/null; then
      log_write "[stop] Failed to kill owned process group ${pid}"
      return 1
    fi
    _runtime_cleanup_wait "${pid}" || return 1
  fi
  rm -f -- "${pid_file}"
}

# runtime_stop_owned_process - Stop one selected repository process group.
# Globals:
#   RUNTIME_DEPLOYMENT_PID_FILE, RUNTIME_SERVER_PID_FILE.
# Arguments:
#   $1: Repository root. $2: server or deployment.
# Outputs:
#   Writes termination failures to standard error.
# Returns:
#   0 when no selected process remains, non-zero otherwise.
runtime_stop_owned_process() {
  local root_folder="$1"
  local process_owner="$2"
  local pid_file

  case "${process_owner}" in
    server) pid_file="${root_folder}/${RUNTIME_SERVER_PID_FILE}" ;;
    deployment) pid_file="${root_folder}/${RUNTIME_DEPLOYMENT_PID_FILE}" ;;
    *) return 2 ;;
  esac
  _runtime_cleanup_process "${pid_file}"
}

# runtime_stop_owned_processes - Stop all repository-recorded process groups.
# Globals:
#   None.
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes termination failures to standard error.
# Returns:
#   0 when no owned process remains, non-zero otherwise.
runtime_stop_owned_processes() {
  local root_folder="$1"
  local status=0

  runtime_stop_owned_process "${root_folder}" server || status=1
  runtime_stop_owned_process "${root_folder}" deployment || status=1
  return "${status}"
}
