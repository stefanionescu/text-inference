#!/usr/bin/env bash
#
# Write container build and runtime diagnostics to standard error.

# log_write: Print one diagnostic line to standard error, or a blank line for no text.
# Arguments:
#   All arguments: Words of the message.
log_write() {
  local message="$*"

  if [[ -z ${message} ]]; then
    printf '\n' >&2
    return 0
  fi
  printf '%s\n' "${message}" >&2
}
