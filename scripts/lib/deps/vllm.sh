#!/usr/bin/env bash
#
# Install locked vLLM and LLM Compressor environments.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the vLLM and compressor dependency installation workflow.

_VLLM_DEPS_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/lib/deps/uv/environment.sh
source "${_VLLM_DEPS_FOLDER}/uv/environment.sh"
# shellcheck source=scripts/lib/deps/venv.sh
source "${_VLLM_DEPS_FOLDER}/venv.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_VLLM_DEPS_FOLDER}/../foundation/log.sh"

# vllm_install_dependencies: Install runtime and compressor dependencies.
# Globals:
#   QUANT_VENV_FOLDER
#   VENV_FOLDER
# Arguments:
#   None.
# Outputs:
#   Writes installation progress and failures to standard error.
# Returns:
#   0 after both environments are installed, non-zero otherwise.
vllm_install_dependencies() {
  local quant_venv_folder="${QUANT_VENV_FOLDER:?QUANT_VENV_FOLDER is required}"
  local venv_folder="${VENV_FOLDER:?VENV_FOLDER is required}"

  log_write "[vllm] Installing vLLM dependencies"
  uv_apply_lock \
    "${venv_folder}" \
    --extra vllm \
    --no-install-package flashinfer-python \
    --no-install-package flashinfer-cubin || return 1
  log_write "[vllm] Installing FlashInfer for CUDA 13 and Torch 2.11"
  uv_install_packages \
    --prefer-binary \
    --extra-index-url "https://flashinfer.ai/whl/cu130/torch2.11" \
    "flashinfer-python==0.6.13" \
    "flashinfer-cubin==0.6.13" || return 1
  venv_prepare "${quant_venv_folder}" || return 1
  log_write "[vllm] Installing LLM Compressor dependencies"
  uv_apply_lock "${quant_venv_folder}" --extra llmcompressor
}
