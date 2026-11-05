#!/usr/bin/env bash
#
# Run the repository warmup and benchmark integration clients.
# Runtime: Bash 3.2+, macOS and Linux.

set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly SCRIPT_DIR
ROOT_DIR="$(CDPATH='' cd -- "${SCRIPT_DIR}/.." && pwd -P)" || exit 1
readonly ROOT_DIR
export ROOT_DIR

# shellcheck source=scripts/config/defaults.sh
source "${SCRIPT_DIR}/config/defaults.sh"
# shellcheck source=scripts/config/values/deployment.sh
source "${SCRIPT_DIR}/config/values/deployment.sh"
# shellcheck source=scripts/lib/env/runtime.sh
source "${SCRIPT_DIR}/lib/env/runtime.sh"
# shellcheck source=scripts/lib/env/warmup.sh
source "${SCRIPT_DIR}/lib/env/warmup.sh"
# shellcheck source=scripts/lib/runtime/warmup/main.sh
source "${SCRIPT_DIR}/lib/runtime/warmup/main.sh"

# _warmup_usage: Print the warmup command contract.
_warmup_usage() {
  printf '%s\n' \
    "Usage:" \
    "  scripts/warmup.sh [--logs]" \
    "" \
    "Options:" \
    "  --logs  Stream third-party runtime output during warmup." \
    "  -h, --help  Show this help."
}

# main: Initialize and execute the warmup suite.
main() {
  local argument
  local is_help_requested=0
  local is_logging_enabled

  cfg_assign_value is_logging_enabled LOGS_ENABLED "${CFG_LOGS_ENABLED_DEFAULT}"

  for argument in "$@"; do
    case "${argument}" in
      --logs)
        is_logging_enabled=1
        ;;
      -h | --help)
        is_help_requested=1
        ;;
      *)
        printf '[warmup] Unknown argument: %s\n' "${argument}" >&2
        _warmup_usage >&2
        return 2
        ;;
    esac
  done
  if ((is_help_requested == 1)); then
    _warmup_usage
    return 0
  fi
  if [[ ${is_logging_enabled} != "0" && ${is_logging_enabled} != "1" ]]; then
    printf '[warmup] LOGS_ENABLED must be 0 or 1\n' >&2
    return 2
  fi
  LOGS_ENABLED="${is_logging_enabled}"
  export LOGS_ENABLED
  export VENV_DIR="${ROOT_DIR}/${CFG_RUNTIME_VENV_DIR_REL}"
  runtime_initialize_paths "${ROOT_DIR}"
  warmup_initialize_environment "${ROOT_DIR}"
  warmup_run "${ROOT_DIR}"
}

main "$@"
