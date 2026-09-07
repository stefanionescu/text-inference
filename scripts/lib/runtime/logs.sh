#!/usr/bin/env bash
#
# Follow deployment logs while separating server noise produced during warmup.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the tail process and warmup-specific operator log stream.

_RUNTIME_LOGS_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1
# shellcheck source=scripts/lib/runtime/warmup/capture.sh
source "${_RUNTIME_LOGS_DIR}/warmup/capture.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_RUNTIME_LOGS_DIR}/../shared/log.sh"
# _runtime_log_stream_start - Start tail through a private FIFO.
_runtime_log_stream_start() {
  local log_file="$1"
  local temporary_root="${TMPDIR-}"

  [[ -n ${temporary_root} ]] || temporary_root="/tmp"
  _RUNTIME_LOG_STREAM_DIR="$(mktemp -d "${temporary_root}/yap-log.XXXXXX")" || return 1
  _RUNTIME_LOG_STREAM_FIFO="${_RUNTIME_LOG_STREAM_DIR}/stream"
  mkfifo "${_RUNTIME_LOG_STREAM_FIFO}" || return 1
  tail -n +1 -F "${log_file}" >"${_RUNTIME_LOG_STREAM_FIFO}" &
  _RUNTIME_LOG_STREAM_PID=$!
}

# _runtime_log_stream_stop - Stop tail and remove its private FIFO.
# Globals:
#   _RUNTIME_LOG_STREAM_DIR
#   _RUNTIME_LOG_STREAM_FIFO
#   _RUNTIME_LOG_STREAM_PID
# Arguments:
#   None.
# Outputs:
#   None.
# Returns:
#   0 after cleanup, non-zero when cleanup fails.
_runtime_log_stream_stop() {
  local status=0

  if [[ -n ${_RUNTIME_LOG_STREAM_PID-} ]] &&
    kill -0 "${_RUNTIME_LOG_STREAM_PID}" 2>/dev/null; then
    kill -TERM "${_RUNTIME_LOG_STREAM_PID}" 2>/dev/null || status=1
    if wait "${_RUNTIME_LOG_STREAM_PID}" 2>/dev/null; then
      :
    fi
  fi
  if [[ -n ${_RUNTIME_LOG_STREAM_FIFO-} ]]; then
    rm -f -- "${_RUNTIME_LOG_STREAM_FIFO}" || status=1
  fi
  if [[ -n ${_RUNTIME_LOG_STREAM_DIR-} && -d ${_RUNTIME_LOG_STREAM_DIR} ]]; then
    rmdir -- "${_RUNTIME_LOG_STREAM_DIR}" || status=1
  fi
  unset _RUNTIME_LOG_STREAM_DIR _RUNTIME_LOG_STREAM_FIFO _RUNTIME_LOG_STREAM_PID
  return "${status}"
}

# runtime_follow_log - Follow deployment output with warmup-aware filtering.
# Globals:
#   _RUNTIME_LOG_SIGNAL_STATUS
# Arguments:
#   $1: Deployment log file.
#   $2: Warmup process lock.
#   $3: Warmup server-noise capture file.
# Outputs:
#   Writes deployment and warmup status to standard output.
# Returns:
#   The follower or signal status.
runtime_follow_log() {
  local log_file="$1"
  local warmup_lock="$2"
  local capture_file="$3"
  local line is_filter_active=0

  mkdir -p -- "$(dirname -- "${capture_file}")" || return 1
  touch -- "${log_file}" "${capture_file}" || return 1
  _runtime_log_stream_start "${log_file}" || return 1
  _RUNTIME_LOG_SIGNAL_STATUS=0
  trap '_runtime_log_stream_stop' EXIT
  trap '_RUNTIME_LOG_SIGNAL_STATUS=130; _runtime_log_stream_stop' INT
  trap '_RUNTIME_LOG_SIGNAL_STATUS=143; _runtime_log_stream_stop' TERM
  while IFS= read -r line || [[ -n ${line} ]]; do
    if ((is_filter_active == 0)) && warmup_capture_start "${warmup_lock}" "${capture_file}" "${line}"; then
      is_filter_active=1
    fi
    if ((is_filter_active == 0)); then
      if [[ ${LOGS_ENABLED:?LOGS_ENABLED is required} == "1" ]] ||
        log_is_repository_line "${line}"; then
        printf '%s\n' "${line}"
      fi
      continue
    fi
    if [[ ${line} == *"[warmup]"* ]]; then
      printf '%s\n' "${line}"
      if [[ ${line} == *"[warmup] Warmup complete"* ||
        ${line} == *"[warmup] Warmup finished with failures"* ||
        ${line} == *"[warmup] Warmup reported failures"* ]]; then
        warmup_capture_finish "${capture_file}" || return 1
        is_filter_active=0
      fi
    else
      printf '%s\n' "${line}" >>"${capture_file}" || return 1
      if [[ ${LOGS_ENABLED} == "1" ]]; then
        printf '%s\n' "${line}"
      fi
    fi
  done <"${_RUNTIME_LOG_STREAM_FIFO}"
  _runtime_log_stream_stop || return 1
  trap - EXIT INT TERM
  return "${_RUNTIME_LOG_SIGNAL_STATUS}"
}
