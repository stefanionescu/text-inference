#!/usr/bin/env bash
#
# Poll fixed loopback readiness while the owned server remains active.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the bounded network readiness probe for server startup.

_SERVER_READINESS_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/config/defaults.sh
source "${_SERVER_READINESS_DIR}/../../../config/defaults.sh"
# shellcheck source=scripts/config/values/deployment.sh
source "${_SERVER_READINESS_DIR}/../../../config/values/deployment.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_SERVER_READINESS_DIR}/../../shared/log.sh"

# server_wait_ready - Wait for the local readiness endpoint.
# Globals:
#   SERVER_PID
#   WARMUP_PROBE_SCRIPT
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
  local probe_script
  local deadline
  local last_error=""

  cfg_assign_value timeout_seconds WARMUP_TIMEOUT_SECONDS "${CFG_WARMUP_TIMEOUT_SECONDS_DEFAULT}"
  cfg_assign_value \
    poll_interval \
    WARMUP_HEALTH_POLL_INTERVAL_SECONDS \
    "${CFG_WARMUP_HEALTH_POLL_INTERVAL_SECONDS_DEFAULT}"
  cfg_assign_value probe_script WARMUP_PROBE_SCRIPT ""
  [[ -n ${probe_script} ]] || return 2
  deadline=$((SECONDS + timeout_seconds))
  while ((SECONDS <= deadline)); do
    if ! kill -0 "${SERVER_PID:?SERVER_PID is required}" 2>/dev/null; then
      log_write "[server] Server process ${SERVER_PID} exited during startup"
      return 1
    fi
    if last_error="$(bash "${probe_script}" 2>&1 >/dev/null)"; then
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
