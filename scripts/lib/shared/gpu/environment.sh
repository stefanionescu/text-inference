#!/usr/bin/env bash
#
# Export build and runtime values for the detected NVIDIA GPU.
# Runtime: Bash 3.2+, Linux.

_GPU_ENVIRONMENT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/lib/shared/gpu/query.sh
source "${_GPU_ENVIRONMENT_DIR}/query.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_GPU_ENVIRONMENT_DIR}/../log.sh"

# _gpu_architecture_values - Print build values for one supported architecture.
_gpu_architecture_values() {
  case "$1" in
    sm80) printf '8.0+PTX|80|1\n' ;;
    sm86) printf '8.6+PTX|86|\n' ;;
    sm89) printf '8.9+PTX|89|\n' ;;
    sm90) printf '9.0+PTX|90|\n' ;;
    sm100) printf '10.0+PTX|100|\n' ;;
    sm103) printf '10.3+PTX|103|\n' ;;
    sm120) printf '12.0+PTX|120|\n' ;;
    *) return 1 ;;
  esac
}

# gpu_detect - Detect and export the GPU identity.
# Globals:
#   DETECTED_GPU_NAME
#   GPU_SM_ARCH
# Arguments:
#   None.
# Outputs:
#   Writes detection failures to standard error.
# Returns:
#   0 after exporting both values, non-zero when detection fails.
gpu_detect() {
  GPU_SM_ARCH="$(gpu_architecture)" || return 1
  DETECTED_GPU_NAME="$(gpu_name)" || return 1
  export DETECTED_GPU_NAME GPU_SM_ARCH
}

# gpu_apply_environment - Export build values for the detected architecture.
# Globals:
#   CUDAARCHS
#   CUDA_DEVICE_MAX_CONNECTIONS
#   GPU_SM_ARCH
#   PYTORCH_CUDA_ALLOC_CONF
#   TORCH_CUDA_ARCH_LIST
# Arguments:
#   None.
# Outputs:
#   Writes unsupported architecture errors to standard error.
# Returns:
#   0 after exporting build values, non-zero for an unsupported architecture.
gpu_apply_environment() {
  local architecture_values
  local architecture_list
  local cuda_architectures
  local maximum_connections

  architecture_values="$(_gpu_architecture_values "${GPU_SM_ARCH:?GPU_SM_ARCH is required}")" || {
    log_write "[gpu] Unsupported GPU architecture: ${GPU_SM_ARCH}"
    return 1
  }
  IFS='|' read -r architecture_list cuda_architectures maximum_connections <<<"${architecture_values}"
  TORCH_CUDA_ARCH_LIST="${architecture_list}"
  CUDAARCHS="${cuda_architectures}"
  PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
  if [[ -n ${maximum_connections} ]]; then
    CUDA_DEVICE_MAX_CONNECTIONS="${maximum_connections}"
    export CUDA_DEVICE_MAX_CONNECTIONS
  fi
  export CUDAARCHS PYTORCH_CUDA_ALLOC_CONF TORCH_CUDA_ARCH_LIST
}
