#!/usr/bin/env bash
#
# Format warmup log paths and report probe results.
# Runtime: Bash 3.2+, macOS and Linux.

_WARMUP_LOGGING_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/runtime.sh
source "${_WARMUP_LOGGING_FOLDER}/../../../config/values/runtime.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_WARMUP_LOGGING_FOLDER}/../../foundation/log.sh"

# warmup_log_prefix - Print a filesystem-safe probe label.
# Globals:
#   None.
# Arguments:
#   $1: Human-readable probe label.
# Outputs:
#   Writes a lowercase underscore-delimited label.
# Returns:
#   0 after writing a non-empty label.
warmup_log_prefix() {
  local raw="$1"
  local cleaned

  cleaned="$(tr '[:upper:]' '[:lower:]' <<<"${raw}")" || return 1
  cleaned="$(tr -c 'a-z0-9' '_' <<<"${cleaned}")" || return 1
  cleaned="${cleaned%_}"
  [[ -n ${cleaned} ]] || cleaned="run"
  printf '%s\n' "${cleaned}"
}

# warmup_phase_result - Report one probe result to operator and server logs.
# Globals:
#   RUNTIME_SERVER_LOG_FILE
#   ROOT_FOLDER
# Arguments:
#   $1: Probe label.
#   $2: OK or FAIL.
#   $3: Optional detailed log path.
# Outputs:
#   Writes one status line to stderr and the server log.
# Returns:
#   0 after reporting.
warmup_phase_result() {
  local label="$1"
  local status="$2"
  local detail="${3-}"
  local line="[warmup] ${label} (${status})"

  if [[ -n ${detail} ]]; then
    line="${line} (see ${detail})"
  fi
  log_write "${line}"
  printf '%s\n' "${line}" >>"${ROOT_FOLDER:?ROOT_FOLDER is required}/${RUNTIME_SERVER_LOG_FILE}"
}
