#!/usr/bin/env bash
#
# Start the owned uvicorn server and run its warmup suite.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

STEP_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly STEP_FOLDER
ROOT_FOLDER="$(CDPATH='' cd -- "${STEP_FOLDER}/../.." && pwd -P)" || exit 1
readonly ROOT_FOLDER
export ROOT_FOLDER

# shellcheck source=scripts/lib/runtime/cleanup/main.sh
source "${STEP_FOLDER}/../lib/runtime/cleanup/main.sh"
# shellcheck source=scripts/lib/runtime/server/readiness.sh
source "${STEP_FOLDER}/../lib/runtime/server/readiness.sh"
# shellcheck source=scripts/lib/runtime/server/process.sh
source "${STEP_FOLDER}/../lib/runtime/server/process.sh"
# shellcheck source=scripts/lib/runtime/records.sh
source "${STEP_FOLDER}/../lib/runtime/records.sh"
# shellcheck source=scripts/lib/foundation/deployment.sh
source "${STEP_FOLDER}/../lib/foundation/deployment.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${STEP_FOLDER}/../lib/foundation/log.sh"

# _server_report_started: Print server ownership and health details.
_server_report_started() {
  log_write "[server] Server started with PID ${SERVER_PID}"
  log_write "[server] Readiness: http://127.0.0.1:8001/readyz"
  log_write "[server] Logs: ${ROOT_FOLDER}/server.log"
}

# _server_run_warmup: Run warmup without turning probe failures into startup failure.
_server_run_warmup() {
  if ! "${STEP_FOLDER}/../warmup.sh"; then
    log_write "[warmup] Warmup reported failures; inspect logs/warmup.log"
  fi
}

# main: Validate, start, persist, and warm the server.
main() {
  deployment_validate_cuda "server"
  server_guard_start "${ROOT_FOLDER}"
  server_start "${ROOT_FOLDER}"
  if ! server_wait_ready; then
    log_write "[server] Startup failed; detailed diagnostics: ${ROOT_FOLDER}/${RUNTIME_SERVER_LOG_FILE}"
    runtime_stop_owned_process "${ROOT_FOLDER}" server
    return 1
  fi
  runtime_state_write "${ROOT_FOLDER}"
  _server_report_started
  _server_run_warmup
}

main "$@"
