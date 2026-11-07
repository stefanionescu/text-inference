#!/usr/bin/env bash
#
# Start detached deployment commands and follow their shared runtime log.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns detached process creation for host deployment workflows.

_RUNTIME_BACKGROUND_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/deployment.sh
source "${_RUNTIME_BACKGROUND_FOLDER}/../../config/values/deployment.sh"
# shellcheck source=scripts/config/values/runtime.sh
source "${_RUNTIME_BACKGROUND_FOLDER}/../../config/values/runtime.sh"
# shellcheck source=scripts/lib/runtime/process.sh
source "${_RUNTIME_BACKGROUND_FOLDER}/process.sh"
# shellcheck source=scripts/lib/runtime/logs.sh
source "${_RUNTIME_BACKGROUND_FOLDER}/logs.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_RUNTIME_BACKGROUND_FOLDER}/../foundation/log.sh"

# _runtime_background_log - Prepare and print the runtime log path.
# Globals:
#   MAX_SERVER_LOG_BYTES
#   RUNTIME_RUN_FOLDER
#   RUNTIME_SERVER_LOG_FILE
#   RUNTIME_SERVER_TRIM_FILE
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes the runtime log path to standard output.
# Returns:
#   0 when the log is ready, non-zero on filesystem failure.
_runtime_background_log() {
  local root_folder="$1"
  local run_folder="${root_folder}/${RUNTIME_RUN_FOLDER}"
  local server_log="${root_folder}/${RUNTIME_SERVER_LOG_FILE}"
  local trim_file="${root_folder}/${RUNTIME_SERVER_TRIM_FILE}"
  local size

  mkdir -p -- "${run_folder}" || return 1
  touch -- "${server_log}" || return 1
  size="$(wc -c <"${server_log}")" || return 1
  if ((size > MAX_SERVER_LOG_BYTES)); then
    tail -c "${MAX_SERVER_LOG_BYTES}" "${server_log}" >"${trim_file}" || return 1
    mv -- "${trim_file}" "${server_log}" || return 1
  fi
  printf '%s\n' "${server_log}"
}

# runtime_start_background - Start a detached command and follow its log.
# Globals:
#   RUNTIME_DEPLOYMENT_PID_FILE
# Arguments:
#   $1: Repository root.
#   $2: Startup diagnostic.
#   Remaining arguments: Command and arguments.
# Outputs:
#   Writes startup diagnostics to standard error and follows the runtime log.
# Returns:
#   The log follower status, or non-zero when startup fails.
runtime_start_background() {
  local root_folder="$1"
  local start_message="$2"
  local server_log
  local warmup_capture
  local warmup_lock
  local background_pid

  shift 2
  (($# > 0)) || return 2
  server_log="$(_runtime_background_log "${root_folder}")" || return 1
  warmup_capture="${root_folder}/${RUNTIME_WARMUP_CAPTURE_FILE}"
  warmup_lock="${root_folder}/${RUNTIME_WARMUP_LOCK_FILE}"
  printf '\n' >&2
  log_write "[main] ${start_message}"
  log_write "[main] Control+C stops the log tail; deployment remains active."
  DEPENDENCY_LOG_FILE="-" setsid nohup "$@" </dev/null >>"${server_log}" 2>&1 &
  background_pid=$!
  runtime_write_pid \
    "${root_folder}/${RUNTIME_DEPLOYMENT_PID_FILE}" \
    "${background_pid}" || return 1
  log_write "[main] Deployment started with PID ${background_pid}"
  log_write "[main] Stop with: bash scripts/stop.sh"
  printf '\n' >&2
  runtime_follow_log "${server_log}" "${warmup_lock}" "${warmup_capture}"
}
