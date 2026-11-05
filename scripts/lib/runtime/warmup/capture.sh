#!/usr/bin/env bash
#
# Mark and report warmup-specific server log capture boundaries.
# Runtime: Bash 3.2+, Linux.

_WARMUP_CAPTURE_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/lib/shared/log.sh
source "${_WARMUP_CAPTURE_DIR}/../../shared/log.sh"

# _warmup_capture_active: Report whether the recorded warmup process exists.
# Globals:
#   None.
# Arguments:
#   $1: Warmup lock file.
# Outputs:
#   None.
# Returns:
#   0 for an active recorded process, non-zero otherwise.
_warmup_capture_active() {
  local lock_file="$1"
  local pid

  [[ -f ${lock_file} ]] || return 1
  IFS= read -r pid <"${lock_file}" || return 1
  [[ ${pid} =~ ^[1-9][0-9]*$ ]] || return 1
  kill -0 "${pid}" 2>/dev/null
}

# warmup_capture_start: Detect warmup and start its detailed capture.
# Globals:
#   None.
# Arguments:
#   $1: Warmup lock. $2: Capture file. $3: Current server log line.
# Outputs:
#   Writes a timestamp boundary to the capture file.
# Returns:
#   0 when warmup starts, 1 when inactive, or another write failure status.
warmup_capture_start() {
  local warmup_lock="$1"
  local capture_file="$2"
  local line="$3"

  if ! _warmup_capture_active "${warmup_lock}" &&
    [[ ${line} != *"[warmup] Starting GPU warmup"* ]]; then
    return 1
  fi
  date '+===== Warmup started at %Y-%m-%d %H:%M:%S %Z =====' \
    >>"${capture_file}"
}

# warmup_capture_finish: Mark and report completed warmup capture.
# Globals:
#   None.
# Arguments:
#   $1: Warmup server-noise capture file.
# Outputs:
#   Writes a timestamp boundary and detailed log path.
# Returns:
#   0 after reporting, non-zero on write failure.
warmup_capture_finish() {
  local capture_file="$1"

  date '+===== Warmup finished at %Y-%m-%d %H:%M:%S %Z =====' >>"${capture_file}" || return 1
  log_write "[warmup] Detailed server logs: ${capture_file}"
}
