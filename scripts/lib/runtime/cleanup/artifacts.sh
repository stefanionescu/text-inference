#!/usr/bin/env bash
#
# Remove repository-owned model, engine, environment, and runtime artifacts.
# Runtime: Bash 3.2+, macOS and Linux.
# Boundary: Owns destructive cleanup below the verified repository root.

_RUNTIME_ARTIFACTS_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/config/values/runtime.sh
source "${_RUNTIME_ARTIFACTS_DIR}/../../../config/values/runtime.sh"
# shellcheck source=scripts/lib/runtime/cleanup/paths.sh
source "${_RUNTIME_ARTIFACTS_DIR}/paths.sh"

# _runtime_clear_owned_paths - Remove repository-relative paths.
_runtime_clear_owned_paths() {
  local root_dir="$1"
  local relative_path
  local status=0

  shift
  for relative_path in "$@"; do
    runtime_remove_owned_path \
      "${root_dir}" "${root_dir}/${relative_path}" || status=1
  done
  return "${status}"
}

# _runtime_clear_model_artifacts - Clear model data and engine runtime caches.
# Globals:
#   None.
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 when every owned path is removed, non-zero otherwise.
_runtime_clear_model_artifacts() {
  local root_dir="$1"

  _runtime_clear_owned_paths \
    "${root_dir}" \
    ".compressed-tensors" \
    ".flashinfer" \
    ".hf" \
    ".modelopt-repo" \
    ".torch_inductor" \
    ".triton" \
    ".trt_cache" \
    ".vllm_cache" \
    ".xformers" \
    "models"
}

# runtime_clear_model_transition - Clear runtime caches while retaining
# repository exports long enough for their provenance validator to decide reuse.
# Globals:
#   None.
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 when every selected artifact is removed, non-zero otherwise.
runtime_clear_model_transition() {
  local root_dir="$1"

  _runtime_clear_owned_paths \
    "${root_dir}" \
    ".flashinfer" \
    ".hf" \
    ".modelopt-repo" \
    ".torch_inductor" \
    ".triton" \
    ".vllm_cache" \
    ".xformers" \
    "models"
}

# runtime_clear_engine_artifacts - Clear model data and incompatible environments.
# Globals:
#   None.
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 when every owned path is removed, non-zero otherwise.
runtime_clear_engine_artifacts() {
  local root_dir="$1"
  local status=0

  _runtime_clear_model_artifacts "${root_dir}" || status=1
  _runtime_clear_owned_paths \
    "${root_dir}" \
    ".pip_cache" \
    ".venv" \
    ".venv-quant" || status=1
  return "${status}"
}

# runtime_clear_reset_artifacts - Clear all repository deployment state.
# Globals:
#   CFG_RUNTIME_LOG_DIR and runtime path constants.
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 when every owned path is removed, non-zero otherwise.
runtime_clear_reset_artifacts() {
  local root_dir="$1"
  local status=0

  runtime_clear_engine_artifacts "${root_dir}" || status=1
  _runtime_clear_owned_paths \
    "${root_dir}" \
    "${CFG_RUNTIME_RUN_DIR}" \
    "${CFG_RUNTIME_LOG_DIR}" \
    "${CFG_RUNTIME_SERVER_PID_FILE}" \
    "${CFG_RUNTIME_SERVER_LOG_FILE}" \
    "${CFG_RUNTIME_SERVER_LOG_TRIM_FILE}" || status=1
  return "${status}"
}
