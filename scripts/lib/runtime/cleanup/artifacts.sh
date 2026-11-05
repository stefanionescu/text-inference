#!/usr/bin/env bash
#
# Remove repository-owned model, engine, environment, and runtime artifacts.
# Runtime: Bash 3.2+, macOS and Linux.
# Boundary: Owns destructive cleanup below the verified repository root.

_RUNTIME_ARTIFACTS_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/runtime.sh
source "${_RUNTIME_ARTIFACTS_FOLDER}/../../../config/values/runtime.sh"
# shellcheck source=scripts/lib/runtime/cleanup/paths.sh
source "${_RUNTIME_ARTIFACTS_FOLDER}/paths.sh"

# _runtime_clear_owned_paths: Remove repository-relative paths.
_runtime_clear_owned_paths() {
  local root_folder="$1"
  local relative_path
  local status=0

  shift
  for relative_path in "$@"; do
    runtime_remove_owned_path \
      "${root_folder}" "${root_folder}/${relative_path}" || status=1
  done
  return "${status}"
}

# runtime_clear_model_transition: Clear runtime caches while retaining
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
  local root_folder="$1"

  _runtime_clear_owned_paths \
    "${root_folder}" \
    ".flashinfer" \
    ".hf" \
    ".modelopt-repo" \
    ".torch_inductor" \
    ".triton" \
    ".vllm_cache" \
    ".xformers" \
    "models"
}

# runtime_clear_engine_artifacts: Clear model data and incompatible environments.
# Globals:
#   None.
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 when every owned path is removed, non-zero otherwise.
runtime_clear_engine_artifacts() {
  local root_folder="$1"
  local status=0

  _runtime_clear_owned_paths \
    "${root_folder}" \
    ".compressed-tensors" \
    ".flashinfer" \
    ".hf" \
    ".modelopt-repo" \
    ".torch_inductor" \
    ".triton" \
    ".trt_cache" \
    ".vllm_cache" \
    ".xformers" \
    "models" || status=1
  _runtime_clear_owned_paths \
    "${root_folder}" \
    ".pip_cache" \
    ".venv" \
    ".venv-quant" || status=1
  return "${status}"
}

# runtime_clear_reset_artifacts: Clear all repository deployment state.
# Globals:
#   RUNTIME_LOG_FOLDER and runtime path constants.
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 when every owned path is removed, non-zero otherwise.
runtime_clear_reset_artifacts() {
  local root_folder="$1"
  local status=0

  runtime_clear_engine_artifacts "${root_folder}" || status=1
  _runtime_clear_owned_paths \
    "${root_folder}" \
    "${RUNTIME_RUN_FOLDER}" \
    "${RUNTIME_LOG_FOLDER}" \
    "${RUNTIME_SERVER_PID_FILE}" \
    "${RUNTIME_SERVER_LOG_FILE}" \
    "${RUNTIME_SERVER_TRIM_FILE}" || status=1
  return "${status}"
}
