#!/usr/bin/env bash
#
# Install locked vLLM and LLM Compressor environments.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the vLLM and compressor dependency installation workflow.

_VLLM_DEPS_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/lib/deps/uv/environment.sh
source "${_VLLM_DEPS_DIR}/uv/environment.sh"
# shellcheck source=scripts/lib/deps/venv.sh
source "${_VLLM_DEPS_DIR}/venv.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_VLLM_DEPS_DIR}/../shared/log.sh"

# vllm_install_dependencies - Install runtime and compressor dependencies.
# Globals:
#   QUANT_VENV_DIR
#   VENV_DIR
# Arguments:
#   None.
# Outputs:
#   Writes installation progress and failures to standard error.
# Returns:
#   0 after both environments are installed, non-zero otherwise.
vllm_install_dependencies() {
  local quant_venv_dir="${QUANT_VENV_DIR:?QUANT_VENV_DIR is required}"
  local venv_dir="${VENV_DIR:?VENV_DIR is required}"

  log_write "[vllm] Installing vLLM dependencies"
  uv_apply_lock \
    "${venv_dir}" \
    --extra vllm \
    --no-install-package flashinfer-python \
    --no-install-package flashinfer-cubin || return 1
  log_write "[vllm] Installing FlashInfer for CUDA 13 and Torch 2.11"
  uv_install_packages \
    --prefer-binary \
    --extra-index-url "https://flashinfer.ai/whl/cu130/torch2.11" \
    "flashinfer-python==0.6.13" \
    "flashinfer-cubin==0.6.13" || return 1
  venv_prepare "${quant_venv_dir}" || return 1
  log_write "[vllm] Installing LLM Compressor dependencies"
  uv_apply_lock "${quant_venv_dir}" --extra llmcompressor
}
