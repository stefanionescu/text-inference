#!/usr/bin/env bash
#
# Run one inspected restart workflow inside the shared log capture.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

# shellcheck source=scripts/lib/foundation/folders.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../lib/foundation/folders.sh"
# shellcheck source=scripts/config/values/runtime.sh
source "${SCRIPTS_FOLDER}/config/values/runtime.sh"
# shellcheck source=scripts/lib/restart/workflow.sh
source "${SCRIPTS_FOLDER}/lib/restart/workflow.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${SCRIPTS_FOLDER}/lib/foundation/log.sh"

# _restart_report_exit: Report the captured diagnostics for a failed workflow.
_restart_report_exit() {
  local status=$?

  trap - EXIT
  if ((status != 0)); then
    log_write "[restart] Restart failed; detailed diagnostics: ${ROOT_FOLDER}/${RUNTIME_SERVER_LOG_FILE}"
  fi
  exit "${status}"
}

# main: Run the inspected restart workflow inside the shared capture.
main() {
  (($# == 0)) || return 2

  trap _restart_report_exit EXIT
  restart_execute_selected "${ROOT_FOLDER}" "${SCRIPTS_FOLDER}"
}

main "$@"
