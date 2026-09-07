#!/usr/bin/env bash
#
# Install locked TensorRT and Model Optimizer Python environments.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns TensorRT and Model Optimizer dependency synchronization.

_TRT_INSTALL_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/config/values/trt.sh
source "${_TRT_INSTALL_DIR}/../../../config/values/trt.sh"
# shellcheck source=scripts/lib/deps/uv/environment.sh
source "${_TRT_INSTALL_DIR}/../uv/environment.sh"
# shellcheck source=scripts/lib/deps/venv.sh
source "${_TRT_INSTALL_DIR}/../venv.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_TRT_INSTALL_DIR}/../../shared/log.sh"

# trt_install_dependencies - Install runtime and Model Optimizer dependencies.
# Globals:
#   QUANT_VENV_DIR
#   ROOT_DIR
#   VENV_DIR
# Arguments:
#   None.
# Outputs:
#   Writes installation progress and validation failures to standard error.
# Returns:
#   0 after both environments validate, non-zero otherwise.
trt_install_dependencies() {
  local quant_venv_dir="${QUANT_VENV_DIR:?QUANT_VENV_DIR is required}"
  local venv_dir="${VENV_DIR:?VENV_DIR is required}"

  log_write "[trt] Installing TensorRT dependencies"
  uv_apply_lock "${venv_dir}" --extra trt || return 1
  venv_prepare "${quant_venv_dir}" || return 1
  log_write "[trt] Installing Model Optimizer ${CFG_MODELOPT_PACKAGE_VERSION}"
  uv_apply_lock \
    "${quant_venv_dir}" \
    --group modelopt \
    --no-build-isolation-package flash-attn || return 1
  log_write "[trt] Validating TensorRT ${CFG_TRT_VERSION}"
  PYTHONPATH="${ROOT_DIR:?ROOT_DIR is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${venv_dir}/bin/python" -m src.scripts.validation.trt
}
