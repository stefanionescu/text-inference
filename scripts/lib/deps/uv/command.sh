#!/usr/bin/env bash
#
# Run uv commands and preserve actionable failure output.
# Runtime: Bash 3.2+, macOS and Linux.
# Boundary: Owns temporary uv command logs and failure reporting.

_UV_COMMAND_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/lib/shared/log.sh
source "${_UV_COMMAND_DIR}/../../shared/log.sh"

# _uv_log_path - Print the persistent uv failure log path.
_uv_log_path() {
  local base_dir="${ROOT_DIR-}"

  [[ -n ${base_dir} ]] || base_dir="${PWD}"
  if [[ -n ${UV_INSTALL_LOG-} ]]; then
    printf '%s\n' "${UV_INSTALL_LOG}"
  else
    printf '%s\n' "${base_dir}/logs/uv-install.log"
  fi
}

# _uv_report_failure - Append one uv failure and print its final lines.
# Globals:
#   None.
# Arguments:
#   $1: Temporary command log.
#   $2: Command status.
#   Remaining arguments: uv arguments.
# Outputs:
#   Appends a persistent log and writes a summary to standard error.
# Returns:
#   0 after reporting, non-zero on log filesystem failure.
_uv_report_failure() {
  local temporary_log="$1"
  local status="$2"
  local log_file
  local log_dir
  local timestamp

  shift 2
  log_file="$(_uv_log_path)" || return 1
  log_dir="$(dirname -- "${log_file}")" || return 1
  timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')" || return 1
  mkdir -p -- "${log_dir}" || return 1
  {
    printf '===== %s\n' "${timestamp}"
    printf 'uv command: uv'
    printf ' %q' "$@"
    printf '\n'
    sed -n '1,$p' "${temporary_log}"
    printf '===== exit code: %s\n' "${status}"
  } >>"${log_file}" || return 1
  log_write "[uv] Command failed; see ${log_file}"
  tail -n 60 "${temporary_log}" >&2
}

# uv_run - Run one uv command with captured failure output.
# Globals:
#   None.
# Arguments:
#   uv arguments.
# Outputs:
#   Writes uv failure details to standard error.
# Returns:
#   The uv status, or non-zero when local logging fails.
uv_run() {
  local temporary_log
  local status

  (($# > 0)) || return 2
  command -v uv >/dev/null 2>&1 || return 127
  temporary_log="$(mktemp -t yap-uv.XXXXXX)" || return 1
  if uv "$@" >"${temporary_log}" 2>&1; then
    rm -f -- "${temporary_log}"
    return 0
  else
    status=$?
  fi
  _uv_report_failure "${temporary_log}" "${status}" "$@" || {
    rm -f -- "${temporary_log}"
    return 1
  }
  rm -f -- "${temporary_log}"
  return "${status}"
}
