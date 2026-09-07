#!/usr/bin/env bash
#
# Start the owned uvicorn server and run its warmup suite.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

STEP_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly STEP_DIR
ROOT_DIR="$(CDPATH='' cd -- "${STEP_DIR}/../.." && pwd -P)" || exit 1
readonly ROOT_DIR
export ROOT_DIR

# shellcheck source=scripts/lib/runtime/cleanup/main.sh
source "${STEP_DIR}/../lib/runtime/cleanup/main.sh"
# shellcheck source=scripts/lib/runtime/server/readiness.sh
source "${STEP_DIR}/../lib/runtime/server/readiness.sh"
# shellcheck source=scripts/lib/runtime/server/process.sh
source "${STEP_DIR}/../lib/runtime/server/process.sh"
# shellcheck source=scripts/lib/runtime/records.sh
source "${STEP_DIR}/../lib/runtime/records.sh"
# shellcheck source=scripts/lib/shared/deployment.sh
source "${STEP_DIR}/../lib/shared/deployment.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${STEP_DIR}/../lib/shared/log.sh"

# _server_report_started - Print server ownership and health details.
_server_report_started() {
  log_write "[server] Server started with PID ${SERVER_PID}"
  log_write "[server] Readiness: http://127.0.0.1:8001/readyz"
  log_write "[server] Logs: ${ROOT_DIR}/server.log"
}

# _server_run_warmup - Run warmup without turning probe failures into startup failure.
_server_run_warmup() {
  if ! "${STEP_DIR}/../warmup.sh"; then
    log_write "[warmup] Warmup reported failures; inspect logs/warmup.log"
  fi
}

# main - Validate, start, persist, and warm the server.
main() {
  deployment_validate_cuda "server"
  server_guard_start "${ROOT_DIR}"
  server_start "${ROOT_DIR}"
  if ! server_wait_ready; then
    log_write "[server] Startup failed; detailed diagnostics: ${ROOT_DIR}/${CFG_RUNTIME_SERVER_LOG_FILE}"
    runtime_stop_owned_process "${ROOT_DIR}" server
    return 1
  fi
  runtime_state_write "${ROOT_DIR}"
  _server_report_started
  _server_run_warmup
}

main "$@"
