#!/usr/bin/env bash
#
# Read and atomically write non-executable runtime deployment records.
# Runtime: Bash 3.2+, macOS and Linux.
# Boundary: Owns the persisted runtime state format and atomic replacement.

_RUNTIME_STATE_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/runtime.sh
source "${_RUNTIME_STATE_DIR}/../../config/values/runtime.sh"

# _runtime_state_key: Validate one state key.
_runtime_state_key() {
  local key="$1"

  case "${key}" in
    EXPORT_PROVENANCE | GPU_SM_ARCH | INFERENCE_ENGINE | KV_DTYPE | REQUESTED_QUANTIZATION | \
      RESOLVED_CHECKPOINT | RUNTIME_QUANTIZATION | SOURCE_MODEL | SOURCE_REVISION)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# _runtime_state_value: Validate one state value for the TSV format.
_runtime_state_value() {
  local value="$1"

  [[ ${value} != *$'\t'* ]] || return 1
  [[ ${value} != *$'\n'* ]] || return 1
  [[ ${value} != *$'\r'* ]]
}

# runtime_state_read: Print one value from the persisted runtime state.
# Globals:
#   CFG_RUNTIME_STATE_FILE
# Arguments:
#   $1: Repository root.
#   $2: Exact state key.
# Outputs:
#   Writes the requested value to standard output.
# Returns:
#   0 for valid or absent state, non-zero for an invalid key or malformed file.
runtime_state_read() {
  local root_dir="$1"
  local requested_key="$2"
  local state_file="${root_dir}/${CFG_RUNTIME_STATE_FILE}"
  local key
  local value
  local remainder
  local requested_value=""
  local seen_keys="|"

  _runtime_state_key "${requested_key}" || return 2
  [[ -f ${state_file} ]] || {
    printf '\n'
    return 0
  }
  while IFS=$'\t' read -r key value remainder || [[ -n ${key}${value}${remainder} ]]; do
    [[ -z ${remainder} ]] || return 1
    _runtime_state_key "${key}" || return 1
    _runtime_state_value "${value}" || return 1
    [[ ${seen_keys} != *"|${key}|"* ]] || return 1
    seen_keys="${seen_keys}${key}|"
    if [[ ${key} == "${requested_key}" ]]; then
      requested_value="${value}"
    fi
  done <"${state_file}"
  printf '%s\n' "${requested_value}"
}

# runtime_state_write: Atomically persist the active runtime configuration.
# Globals:
#   CFG_RUNTIME_RUN_DIR
#   CFG_RUNTIME_STATE_FILE
#   GPU_SM_ARCH
#   INFERENCE_ENGINE
#   KV_DTYPE
#   SOURCE_MODEL
#   SOURCE_REVISION
#   RESOLVED_CHECKPOINT
#   RUNTIME_QUANTIZATION
#   REQUESTED_QUANTIZATION
#   EXPORT_PROVENANCE
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 after atomic replacement, non-zero on validation or filesystem failure.
runtime_state_write() {
  local root_dir="$1"
  local run_dir="${root_dir}/${CFG_RUNTIME_RUN_DIR}"
  local state_file="${root_dir}/${CFG_RUNTIME_STATE_FILE}"
  local value

  for value in \
    "${GPU_SM_ARCH:?GPU_SM_ARCH is required}" \
    "${INFERENCE_ENGINE:?INFERENCE_ENGINE is required}" \
    "${KV_DTYPE:?KV_DTYPE is required}" \
    "${SOURCE_MODEL:?SOURCE_MODEL is required}" \
    "${SOURCE_REVISION:?SOURCE_REVISION is required}" \
    "${RESOLVED_CHECKPOINT:?RESOLVED_CHECKPOINT is required}" \
    "${RUNTIME_QUANTIZATION-}" \
    "${REQUESTED_QUANTIZATION-}" \
    "${EXPORT_PROVENANCE-}"; do
    _runtime_state_value "${value}" || return 2
  done
  mkdir -p -- "${run_dir}" || return 1
  (
    local temporary_file

    umask 077
    temporary_file="$(mktemp "${state_file}.XXXXXX")" || exit 1
    trap 'rm -f -- "${temporary_file}"' EXIT
    {
      printf 'GPU_SM_ARCH\t%s\n' "${GPU_SM_ARCH}"
      printf 'INFERENCE_ENGINE\t%s\n' "${INFERENCE_ENGINE}"
      printf 'KV_DTYPE\t%s\n' "${KV_DTYPE}"
      printf 'SOURCE_MODEL\t%s\n' "${SOURCE_MODEL}"
      printf 'SOURCE_REVISION\t%s\n' "${SOURCE_REVISION}"
      printf 'RESOLVED_CHECKPOINT\t%s\n' "${RESOLVED_CHECKPOINT}"
      printf 'RUNTIME_QUANTIZATION\t%s\n' "${RUNTIME_QUANTIZATION-}"
      printf 'REQUESTED_QUANTIZATION\t%s\n' "${REQUESTED_QUANTIZATION-}"
      printf 'EXPORT_PROVENANCE\t%s\n' "${EXPORT_PROVENANCE-}"
    } >"${temporary_file}" || exit 1
    mv -- "${temporary_file}" "${state_file}" || exit 1
    trap - EXIT
  )
}
