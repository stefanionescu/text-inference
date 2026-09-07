#!/usr/bin/env bash
#
# Run one engine server, raw capture, filtered console, and readiness warmup.

# shellcheck source=scripts/lib/shared/log.sh
source "/app/scripts/lib/shared/log.sh"

# container_show_usage - Print the fixed Docker runtime interface.
# Globals:
#   None.
# Arguments:
#   None.
# Outputs:
#   Writes usage to standard output.
# Returns:
#   0 after writing usage.
container_show_usage() {
  cat <<'EOF'
Usage: /app/scripts/main.sh [--logs]

Requires API_KEY. The image runs its baked checkpoint unchanged, exposes the
WebSocket service on port 8000, and keeps readiness on loopback port 8001.
EOF
}

_container_follow_log() {
  local log_file="$1"
  local server_pid="$2"
  local pipe_dir
  local pipe_path
  local tail_pid
  local tail_status=0
  local line

  pipe_dir="$(mktemp -d /tmp/yap-log.XXXXXX)" || return 1
  pipe_path="${pipe_dir}/stream"
  mkfifo "${pipe_path}" || {
    rmdir "${pipe_dir}"
    return 1
  }
  tail --pid="${server_pid}" -n +1 -F "${log_file}" >"${pipe_path}" &
  tail_pid=$!
  while IFS= read -r line || [[ -n ${line} ]]; do
    if [[ ${LOGS_ENABLED:?LOGS_ENABLED is required} == "1" ]] ||
      log_is_repository_line "${line}"; then
      printf '%s\n' "${line}"
    fi
  done <"${pipe_path}"
  wait "${tail_pid}" || tail_status=$?
  rm -f -- "${pipe_path}" || return 1
  rmdir "${pipe_dir}" || return 1
  return "${tail_status}"
}

# start_warmup_server - Start one dual-listener engine server and warmup probe.
start_warmup_server() {
  local engine="$1"
  local server_module="$2"
  local server_log="/app/server.log"
  local server_pid
  local follower_pid
  local server_status

  cd /app || return 1
  touch "${server_log}" || return 1
  log_write "[${engine}] Starting server"
  DEPENDENCY_LOG_FILE="-" \
    "${VENV_DIR:?VENV_DIR is required}/bin/python" -m "${server_module}" \
    >>"${server_log}" 2>&1 &
  server_pid=$!
  trap 'if kill -0 "${server_pid}" 2>/dev/null; then kill -TERM "${server_pid}"; fi' INT TERM
  _container_follow_log "${server_log}" "${server_pid}" &
  follower_pid=$!
  /app/shared/scripts/warmup.sh &
  set +e
  wait "${server_pid}"
  server_status=$?
  set -e
  wait "${follower_pid}"
  trap - INT TERM
  if ((server_status != 0)); then
    log_write "[${engine}] Server failed; detailed diagnostics: ${server_log}"
  fi
  return "${server_status}"
}
