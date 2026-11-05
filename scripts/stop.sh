#!/usr/bin/env bash
#
# Stop repository-owned processes or explicitly reset the inference host.
# Runtime: Bash 3.2+, macOS and Linux.

set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly SCRIPT_DIR
ROOT_DIR="$(CDPATH='' cd -- "${SCRIPT_DIR}/.." && pwd -P)" || exit 1
readonly ROOT_DIR

# shellcheck source=scripts/config/messages/stop.sh
source "${SCRIPT_DIR}/config/messages/stop.sh"
# shellcheck source=scripts/lib/runtime/cleanup/main.sh
source "${SCRIPT_DIR}/lib/runtime/cleanup/main.sh"
# shellcheck source=scripts/lib/runtime/cleanup/reset.sh
source "${SCRIPT_DIR}/lib/runtime/cleanup/reset.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${SCRIPT_DIR}/lib/shared/log.sh"

# _stop_usage: Print the stop command contract.
_stop_usage() {
  local status="$1"
  local line

  for line in "${CFG_STOP_USAGE_LINES[@]}"; do
    printf '%s\n' "${line}"
  done
  exit "${status}"
}

# _stop_parse_args: Parse the exact stop command contract.
_stop_parse_args() {
  STOP_RESET_REQUESTED=0
  case "$#" in
    0) ;;
    1)
      case "$1" in
        --reset) STOP_RESET_REQUESTED=1 ;;
        --help | -h) _stop_usage 0 ;;
        *) return 2 ;;
      esac
      ;;
    *) return 2 ;;
  esac
}

# main: Stop owned processes or run the explicit reset.
main() {
  _stop_parse_args "$@" || _stop_usage 2
  if [[ ${STOP_RESET_REQUESTED} == "1" ]]; then
    log_write "${CFG_STOP_MSG_RESET}"
    runtime_reset_host "${ROOT_DIR}"
    log_write "${CFG_STOP_MSG_RESET_DONE}"
    return 0
  fi
  log_write "${CFG_STOP_MSG_STOP}"
  runtime_stop_owned_processes "${ROOT_DIR}"
  log_write "${CFG_STOP_MSG_STOP_DONE}"
}

main "$@"
