#!/usr/bin/env bash
#
# Prepare the pinned NVIDIA Model Optimizer source checkout.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the external Model Optimizer git checkout.

_TRT_MODELOPT_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/trt.sh
source "${_TRT_MODELOPT_FOLDER}/../../config/values/trt.sh"
# shellcheck source=scripts/lib/runtime/cleanup/paths.sh
source "${_TRT_MODELOPT_FOLDER}/../../lib/runtime/cleanup/paths.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_TRT_MODELOPT_FOLDER}/../../lib/foundation/log.sh"

# trt_prepare_modelopt: Clone and verify the pinned Model Optimizer revision.
# Globals:
#   MODELOPT_COMMIT
#   MODELOPT_REPO_URL
#   MODELOPT_TAG
#   MODELOPT_REPO_FOLDER
#   ROOT_FOLDER
# Arguments:
#   None.
# Outputs:
#   Writes checkout progress and validation failures to standard error.
# Returns:
#   0 for the exact checkout, non-zero otherwise.
trt_prepare_modelopt() {
  local modelopt_folder="${MODELOPT_REPO_FOLDER:?MODELOPT_REPO_FOLDER is required}"
  local installed_version
  local revision=""

  if [[ -d ${modelopt_folder}/.git ]]; then
    revision="$(git -C "${modelopt_folder}" rev-parse HEAD)" || return 1
    if [[ ${revision} == "${MODELOPT_COMMIT}" ]]; then
      installed_version="$("${QUANT_VENV_FOLDER:?QUANT_VENV_FOLDER is required}/bin/python" -c \
        'import importlib.metadata; print(importlib.metadata.version("nvidia-modelopt"))')" || return 1
      [[ ${installed_version} == "${MODELOPT_PACKAGE_VERSION}" ]] || {
        log_write "[trt] Model Optimizer package version mismatch: ${installed_version}"
        return 1
      }
      return 0
    fi
  fi
  runtime_remove_owned_path "${ROOT_FOLDER:?ROOT_FOLDER is required}" "${modelopt_folder}" || return 1
  log_write "[trt] Cloning NVIDIA Model Optimizer ${MODELOPT_TAG}"
  git -c advice.detachedHead=false clone \
    --quiet --single-branch --branch "${MODELOPT_TAG}" \
    --depth 1 --filter=blob:none \
    "${MODELOPT_REPO_URL}" "${modelopt_folder}" || return 1
  revision="$(git -C "${modelopt_folder}" rev-parse HEAD)" || return 1
  if [[ ${revision} != "${MODELOPT_COMMIT}" ]]; then
    log_write "[trt] Model Optimizer revision mismatch: ${revision}"
    return 1
  fi
  [[ -f ${modelopt_folder}/examples/llm_ptq/hf_ptq.py ]] || return 1
  installed_version="$("${QUANT_VENV_FOLDER}/bin/python" -c \
    'import importlib.metadata; print(importlib.metadata.version("nvidia-modelopt"))')" || return 1
  if [[ ${installed_version} != "${MODELOPT_PACKAGE_VERSION}" ]]; then
    log_write "[trt] Model Optimizer package version mismatch: ${installed_version}"
    return 1
  fi
}
