#!/usr/bin/env bash
#
# Install locked TensorRT and Model Optimizer Python environments.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns TensorRT and Model Optimizer dependency synchronization.

_TRT_INSTALL_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/trt.sh
source "${_TRT_INSTALL_FOLDER}/../../../config/values/trt.sh"
# shellcheck source=scripts/lib/deps/uv/environment.sh
source "${_TRT_INSTALL_FOLDER}/../uv/environment.sh"
# shellcheck source=scripts/lib/deps/venv.sh
source "${_TRT_INSTALL_FOLDER}/../venv.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_TRT_INSTALL_FOLDER}/../../foundation/log.sh"

# trt_install_dependencies - Install runtime and Model Optimizer dependencies.
# Globals:
#   QUANT_VENV_FOLDER
#   ROOT_FOLDER
#   VENV_FOLDER
# Arguments:
#   None.
# Outputs:
#   Writes installation progress and validation failures to standard error.
# Returns:
#   0 after both environments validate, non-zero otherwise.
trt_install_dependencies() {
  local quant_venv_folder="${QUANT_VENV_FOLDER:?QUANT_VENV_FOLDER is required}"
  local venv_folder="${VENV_FOLDER:?VENV_FOLDER is required}"

  log_write "[trt] Installing TensorRT dependencies"
  uv_apply_lock "${venv_folder}" --extra trt || return 1
  venv_prepare "${quant_venv_folder}" || return 1
  log_write "[trt] Installing Model Optimizer ${MODELOPT_PACKAGE_VERSION}"
  uv_apply_lock \
    "${quant_venv_folder}" \
    --group modelopt \
    --no-build-isolation-package flash-attn || return 1
  log_write "[trt] Validating TensorRT ${TRT_PINNED_VERSION}"
  PYTHONPATH="${ROOT_FOLDER:?ROOT_FOLDER is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${venv_folder}/bin/python" -m src.scripts.validation.trt
}
