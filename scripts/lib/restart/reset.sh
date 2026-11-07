#!/usr/bin/env bash
#
# Capture complete diagnostics for an explicit host reset.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns reset capture across repository log deletion.

_RESTART_RESET_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/runtime.sh
source "${_RESTART_RESET_FOLDER}/../../config/values/runtime.sh"
# shellcheck source=scripts/lib/runtime/cleanup/reset.sh
source "${_RESTART_RESET_FOLDER}/../runtime/cleanup/reset.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_RESTART_RESET_FOLDER}/../foundation/log.sh"

# restart_capture_reset - Run the host reset while retaining raw diagnostics.
# Globals:
#   LOGS_ENABLED, TMPDIR.
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes repository diagnostics, or all diagnostics in raw-log mode.
# Returns:
#   The aggregate host reset status.
restart_capture_reset() {
  local root_folder="$1"
  local temporary_root="${TMPDIR-}"
  local capture_file
  local server_log="${root_folder}/${RUNTIME_SERVER_LOG_FILE}"
  local line
  local status=0

  [[ -n ${temporary_root} ]] || temporary_root="/tmp"
  capture_file="$(mktemp "${temporary_root}/yap-reset.XXXXXX")" || return 1
  trap 'rm -f -- "${capture_file}"; trap - RETURN' RETURN
  runtime_reset_host "${root_folder}" >"${capture_file}" 2>&1 || status=$?
  mv -- "${capture_file}" "${server_log}" || return 1
  while IFS= read -r line || [[ -n ${line} ]]; do
    if [[ ${LOGS_ENABLED:?LOGS_ENABLED is required} == "1" ]] ||
      log_is_repository_line "${line}"; then
      printf '%s\n' "${line}"
    fi
  done <"${server_log}"
  if ((status != 0)); then
    log_write "[restart] Reset failed; detailed diagnostics: ${server_log}"
  fi
  return "${status}"
}
