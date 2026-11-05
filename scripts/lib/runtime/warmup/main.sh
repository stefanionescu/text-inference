#!/usr/bin/env bash
#
# Coordinate warmup process ownership and integration probes.
# Runtime: Bash 3.2+, macOS and Linux.

_WARMUP_MAIN_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/runtime.sh
source "${_WARMUP_MAIN_DIR}/../../../config/values/runtime.sh"
# shellcheck source=scripts/lib/runtime/warmup/logging.sh
source "${_WARMUP_MAIN_DIR}/logging.sh"
# shellcheck source=scripts/lib/runtime/warmup/profile.sh
source "${_WARMUP_MAIN_DIR}/profile.sh"
# shellcheck source=scripts/lib/runtime/warmup/suite.sh
source "${_WARMUP_MAIN_DIR}/suite.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_WARMUP_MAIN_DIR}/../../shared/log.sh"

# _warmup_connection_limit: Print the validated benchmark connection limit.
_warmup_connection_limit() {
  if [[ ! ${MAX_CONCURRENT_CONNECTIONS-} =~ ^[1-9][0-9]*$ ]]; then
    log_write "[warmup] MAX_CONCURRENT_CONNECTIONS must be a positive integer"
    return 1
  fi
  printf '%s\n' "${MAX_CONCURRENT_CONNECTIONS}"
}

# _warmup_clear_lock: Remove the lock owned by the active warmup process.
# Globals:
#   WARMUP_ACTIVE_LOCK_FILE
# Arguments:
#   None.
# Outputs:
#   None.
# Returns:
#   The removal status.
_warmup_clear_lock() {
  if [[ -n ${WARMUP_ACTIVE_LOCK_FILE-} ]]; then
    rm -f -- "${WARMUP_ACTIVE_LOCK_FILE}"
  fi
}

# _warmup_report: Append the final suite result.
_warmup_report() {
  local status="$1"
  local message="[warmup] Warmup complete"

  if [[ ${status} != "0" ]]; then
    message="[warmup] Warmup finished with failures"
  fi
  log_write "${message}"
  printf '%s\n' "${message}" >>"${ROOT_DIR:?ROOT_DIR is required}/${CFG_RUNTIME_SERVER_LOG_FILE}"
}

# warmup_run: Own the warmup lock and execute all configured probes.
# Globals:
#   LOG_DIR
#   VENV_DIR
#   WARMUP_LOCK_FILE
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes warmup and benchmark status to operator and log streams.
# Returns:
#   0 when every probe succeeds, non-zero otherwise.
warmup_run() {
  local root_dir="$1"
  local python_bin="${VENV_DIR:?VENV_DIR is required}/bin/python"
  local maximum_connections
  local status=0

  [[ -x ${python_bin} ]] || return 1
  maximum_connections="$(_warmup_connection_limit)" || return 1
  mkdir -p -- "${LOG_DIR:?LOG_DIR is required}" || return 1
  printf '%s\n' "$$" >"${WARMUP_LOCK_FILE:?WARMUP_LOCK_FILE is required}" || return 1
  WARMUP_ACTIVE_LOCK_FILE="${WARMUP_LOCK_FILE}"
  trap '_warmup_clear_lock' EXIT INT TERM
  export PYTHONPATH="${root_dir}${PYTHONPATH:+:${PYTHONPATH}}"
  warmup_detect_profiles "${python_bin}" || return 1
  printf '[warmup] MAX_CONCURRENT_CONNECTIONS=%s\n' \
    "${maximum_connections}" \
    >>"${WARMUP_LOG_FILE:?WARMUP_LOG_FILE is required}" || return 1
  log_write "[warmup] Starting GPU warmup"
  (
    cd -- "${root_dir}" || exit 1
    warmup_run_suite \
      "${maximum_connections}" "${python_bin}" \
      "${WARMUP_PROMPT_PAIRS[@]}"
  ) || status=1
  _warmup_report "${status}"
  _warmup_clear_lock
  trap - EXIT INT TERM
  return "${status}"
}
