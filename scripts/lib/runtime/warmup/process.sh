#!/usr/bin/env bash
#
# Stop the warmup process recorded by the repository lock file.
# Runtime: Bash 3.2+, macOS and Linux.
# Boundary: Owns warmup process termination through its persisted PID.

_WARMUP_PROCESS_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/runtime.sh
source "${_WARMUP_PROCESS_FOLDER}/../../../config/values/runtime.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_WARMUP_PROCESS_FOLDER}/../../foundation/log.sh"

# warmup_stop_existing: Stop the warmup process recorded by the repository.
# Globals:
#   RUNTIME_WARMUP_LOCK_FILE
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes process status to standard error.
# Returns:
#   0 when no recorded process remains, non-zero when termination fails.
warmup_stop_existing() {
  local root_folder="$1"
  local lock_file="${root_folder}/${RUNTIME_WARMUP_LOCK_FILE}"
  local pid
  local attempt

  [[ -f ${lock_file} ]] || return 0
  if ! IFS= read -r pid <"${lock_file}" || [[ ! ${pid} =~ ^[1-9][0-9]*$ ]]; then
    rm -f -- "${lock_file}"
    return 0
  fi
  if ! kill -0 "${pid}" 2>/dev/null; then
    rm -f -- "${lock_file}"
    return 0
  fi
  log_write "[warmup] Stopping existing warmup process ${pid}"
  if ! kill -TERM "${pid}" 2>/dev/null && kill -0 "${pid}" 2>/dev/null; then
    return 1
  fi
  for ((attempt = 0; attempt < 5; attempt++)); do
    if ! kill -0 "${pid}" 2>/dev/null; then
      rm -f -- "${lock_file}"
      return 0
    fi
    sleep 1
  done
  if ! kill -KILL "${pid}" 2>/dev/null && kill -0 "${pid}" 2>/dev/null; then
    return 1
  fi
  rm -f -- "${lock_file}"
}
