#!/usr/bin/env bash
#
# Poll fixed loopback readiness while the owned server remains active.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the bounded network readiness probe for server startup.

_SERVER_READINESS_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_SERVER_READINESS_FOLDER}/../../../config/defaults.sh"
# shellcheck source=scripts/config/values/deployment.sh
source "${_SERVER_READINESS_FOLDER}/../../../config/values/deployment.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_SERVER_READINESS_FOLDER}/../../foundation/log.sh"

# server_wait_ready: Wait for the local readiness endpoint.
# Globals:
#   SERVER_PID
#   WARMUP_READINESS_SCRIPT
#   WARMUP_HEALTH_POLL_INTERVAL_SECONDS
#   WARMUP_TIMEOUT_SECONDS
# Arguments:
#   None.
# Outputs:
#   Writes timeout and process failures to standard error.
# Returns:
#   0 when readiness succeeds, non-zero on process exit or timeout.
server_wait_ready() {
  local timeout_seconds
  local poll_interval
  local readiness_script
  local deadline
  local last_error=""

  config_assign_value timeout_seconds WARMUP_TIMEOUT_SECONDS "${WARMUP_TIMEOUT_SECONDS_DEFAULT}"
  config_assign_value \
    poll_interval \
    WARMUP_HEALTH_POLL_INTERVAL_SECONDS \
    "${WARMUP_HEALTH_POLL_SECONDS}"
  config_assign_value readiness_script WARMUP_READINESS_SCRIPT ""
  [[ -n ${readiness_script} ]] || return 2
  deadline=$((SECONDS + timeout_seconds))
  while ((SECONDS <= deadline)); do
    if ! kill -0 "${SERVER_PID:?SERVER_PID is required}" 2>/dev/null; then
      log_write "[server] Server process ${SERVER_PID} exited during startup"
      return 1
    fi
    if last_error="$(bash "${readiness_script}" 2>&1 >/dev/null)"; then
      return 0
    fi
    sleep "${poll_interval}"
  done
  log_write "[server] Readiness check timed out after ${timeout_seconds}s"
  if [[ -n ${last_error} ]]; then
    log_write "[server] Last readiness error: ${last_error}"
  fi
  return 1
}
