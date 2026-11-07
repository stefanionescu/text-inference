#!/usr/bin/env bash
#
# Write host deployment diagnostics to standard error.
# Runtime: Bash 3.2+, macOS and Linux.

# log_write - Write one non-empty diagnostic line.
# Globals:
#   None.
# Arguments:
#   Message words.
# Outputs:
#   Writes one line to standard error.
# Returns:
#   0 after writing, or 2 for an empty message.
log_write() {
  local message="$*"

  [[ -n ${message} ]] || return 2
  printf '%s\n' "${message}" >&2
  return 0
}

# log_is_repository_line - Identify one repository-owned diagnostic line.
# Globals:
#   None.
# Arguments:
#   $1: Captured output line.
# Outputs:
#   None.
# Returns:
#   0 for repository output, 1 for dependency or native output.
log_is_repository_line() {
  local line="$1"

  case "${line}" in
    "[build]"* | "[certs]"* | "[cuda]"* | "[deploy]"* | "[deps]"* | \
      "[env]"* | "[gpu]"* | "[inspect]"* | "[main]"* | "[python]"* | \
      "[quant]"* | "[reset]"* | "[restart]"* | "[server]"* | "[stop]"* | \
      "[trt]"* | "[uv]"* | "[validate]"* | "[venv]"* | "[vllm]"* | \
      "[warmup]"* | *" name=src"*)
      return 0
      ;;
    *) return 1 ;;
  esac
}
