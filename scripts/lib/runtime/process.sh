#!/usr/bin/env bash
#
# Read and atomically persist repository-owned process identifiers.
# Runtime: Bash 3.2+, macOS and Linux.

# runtime_read_pid - Print a syntactically valid process identifier.
# Globals:
#   None.
# Arguments:
#   $1: PID file.
# Outputs:
#   Writes the process identifier to standard output.
# Returns:
#   0 for a valid PID file, non-zero otherwise.
runtime_read_pid() {
  local pid_file="$1"
  local pid

  [[ -f ${pid_file} ]] || return 1
  IFS= read -r pid <"${pid_file}" || return 1
  [[ ${pid} =~ ^[1-9][0-9]*$ ]] || return 1
  printf '%s\n' "${pid}"
}

# runtime_write_pid - Atomically persist one process identifier.
# Globals:
#   None.
# Arguments:
#   $1: PID file.
#   $2: Process identifier.
# Outputs:
#   None.
# Returns:
#   0 after atomic replacement, non-zero on filesystem failure.
runtime_write_pid() {
  local pid_file="$1"
  local pid="$2"
  local temporary_file

  temporary_file="$(mktemp "${pid_file}.XXXXXX")" || return 1
  trap 'rm -f -- "${temporary_file}"; trap - RETURN' RETURN
  printf '%s\n' "${pid}" >"${temporary_file}" || return 1
  mv -- "${temporary_file}" "${pid_file}" || return 1
}
