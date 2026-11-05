#!/usr/bin/env bash
#
# Run one inspected restart workflow inside the shared log capture.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

DEPLOY_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly DEPLOY_DIR
SCRIPTS_DIR="$(CDPATH='' cd -- "${DEPLOY_DIR}/.." && pwd -P)" || exit 1
readonly SCRIPTS_DIR
ROOT_DIR="$(CDPATH='' cd -- "${SCRIPTS_DIR}/.." && pwd -P)" || exit 1
readonly ROOT_DIR
export ROOT_DIR

# shellcheck source=scripts/config/values/runtime.sh
source "${SCRIPTS_DIR}/config/values/runtime.sh"
# shellcheck source=scripts/lib/restart/workflow.sh
source "${SCRIPTS_DIR}/lib/restart/workflow.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${SCRIPTS_DIR}/lib/shared/log.sh"

# _restart_report_exit: Report the captured diagnostics for a failed workflow.
_restart_report_exit() {
  local status=$?

  trap - EXIT
  if ((status != 0)); then
    log_write "[restart] Restart failed; detailed diagnostics: ${ROOT_DIR}/${CFG_RUNTIME_SERVER_LOG_FILE}"
  fi
  exit "${status}"
}

# main: Run the inspected restart workflow inside the shared capture.
main() {
  (($# == 0)) || return 2

  trap _restart_report_exit EXIT
  restart_execute_selected "${ROOT_DIR}" "${SCRIPTS_DIR}"
}

main "$@"
