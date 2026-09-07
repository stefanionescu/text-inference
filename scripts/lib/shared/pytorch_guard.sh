#!/usr/bin/env bash
#
# Detect a Torch and TorchVision CUDA package mismatch.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the managed Python CUDA package compatibility probe.

_PYTORCH_GUARD_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/lib/shared/log.sh
source "${_PYTORCH_GUARD_DIR}/log.sh"

# pytorch_guard_check - Detect mismatched Torch packages.
# Globals:
#   ROOT_DIR
#   VENV_DIR
# Arguments:
#   $1: Diagnostic prefix.
# Outputs:
#   Writes detection diagnostics to standard error.
# Returns:
#   0 for compatible packages, 42 for a CUDA mismatch, or another probe status.
pytorch_guard_check() {
  local prefix="$1"
  local python_bin="${VENV_DIR:?VENV_DIR is required}/bin/python"
  local output
  local status

  if [[ ! -x ${python_bin} ]]; then
    log_write "${prefix} Managed Python is missing: ${python_bin}"
    return 1
  fi
  if output="$(
    PYTHONPATH="${ROOT_DIR:?ROOT_DIR is required}${PYTHONPATH:+:${PYTHONPATH}}" \
      "${python_bin}" -m src.scripts.guard 2>&1
  )"; then
    return 0
  else
    status=$?
  fi
  if ((status == 42)); then
    log_write "${prefix} Detected a Torch and TorchVision CUDA mismatch"
    if [[ -n ${output} ]]; then
      while IFS= read -r line; do
        [[ -n ${line} ]] && log_write "${prefix} ${line}"
      done <<<"${output}"
    fi
    return 42
  fi
  log_write "${prefix} CUDA package probe failed with status ${status}"
  if [[ -n ${output} ]]; then
    while IFS= read -r line; do
      [[ -n ${line} ]] && log_write "${prefix} ${line}"
    done <<<"${output}"
  fi
  return "${status}"
}
