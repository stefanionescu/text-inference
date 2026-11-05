#!/usr/bin/env bash
#
# Start and identify the repository-owned uvicorn process group.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns detached server process creation and PID persistence.

_SERVER_PROCESS_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/deployment.sh
source "${_SERVER_PROCESS_DIR}/../../../config/values/deployment.sh"
# shellcheck source=scripts/config/values/runtime.sh
source "${_SERVER_PROCESS_DIR}/../../../config/values/runtime.sh"
# shellcheck source=scripts/lib/runtime/process.sh
source "${_SERVER_PROCESS_DIR}/../process.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_SERVER_PROCESS_DIR}/../../shared/log.sh"

# _server_module: Print the selected server process module.
_server_module() {
  case "${INFERENCE_ENGINE:?INFERENCE_ENGINE is required}" in
    trt) printf 'src.server.trt\n' ;;
    vllm) printf 'src.server.vllm\n' ;;
    *)
      log_write "[server] Invalid INFERENCE_ENGINE='${INFERENCE_ENGINE}'"
      return 2
      ;;
  esac
}

# _server_build_command: Assign the managed uvicorn command array.
_server_build_command() {
  local server_module
  local python_bin="${VENV_DIR:?VENV_DIR is required}/bin/python"

  server_module="$(_server_module)" || return 1
  [[ -x ${python_bin} ]] || return 127
  if ! PYTHONPATH="${ROOT_DIR:?ROOT_DIR is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.scripts.validation.package uvicorn >/dev/null 2>&1; then
    log_write "[server] uvicorn is not installed in ${VENV_DIR}"
    return 127
  fi
  SERVER_COMMAND=("${python_bin}" -m "${server_module}")
}

# server_guard_start: Reject startup while an owned server process is active.
# Globals:
#   CFG_RUNTIME_SERVER_PID_FILE
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes stale or active PID diagnostics to standard error.
# Returns:
#   0 when startup is safe, non-zero when the server is already running.
server_guard_start() {
  local root_dir="$1"
  local pid_file="${root_dir}/${CFG_RUNTIME_SERVER_PID_FILE}"
  local pid

  if ! pid="$(runtime_read_pid "${pid_file}")"; then
    rm -f -- "${pid_file}"
    return 0
  fi
  if kill -0 "${pid}" 2>/dev/null; then
    log_write "[server] Server already running with PID ${pid}"
    return 1
  fi
  log_write "[server] Removing stale PID file ${pid_file}"
  rm -f -- "${pid_file}"
}

# server_start: Start uvicorn in a detached process group.
# Globals:
#   CFG_RUNTIME_SERVER_LOG_FILE
#   SERVER_PID
# Arguments:
#   $1: Repository root.
# Outputs:
#   Appends server output to the runtime log.
# Returns:
#   0 after persisting the process identifier, non-zero on failure.
server_start() {
  local root_dir="$1"
  local pid_file="${root_dir}/${CFG_RUNTIME_SERVER_PID_FILE}"
  local server_log="${root_dir}/${CFG_RUNTIME_SERVER_LOG_FILE}"

  _server_build_command || return 1
  PYTHONUNBUFFERED=1 setsid "${SERVER_COMMAND[@]}" >>"${server_log}" 2>&1 &
  SERVER_PID=$!
  export SERVER_PID
  runtime_write_pid "${pid_file}" "${SERVER_PID}"
}
