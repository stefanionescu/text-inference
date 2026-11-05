#!/usr/bin/env bash
#
# Initialize repository-owned host deployment environment values.
# Runtime: Bash 3.2+, Linux.

_DEPLOY_ENVIRONMENT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_DEPLOY_ENVIRONMENT_DIR}/../config/defaults.sh"
# shellcheck source=scripts/config/patterns.sh
source "${_DEPLOY_ENVIRONMENT_DIR}/../config/patterns.sh"
# shellcheck source=scripts/config/values/quantization.sh
source "${_DEPLOY_ENVIRONMENT_DIR}/../config/values/quantization.sh"
# shellcheck source=scripts/lib/env/runtime.sh
source "${_DEPLOY_ENVIRONMENT_DIR}/../lib/env/runtime.sh"
# shellcheck source=scripts/lib/env/trt.sh
source "${_DEPLOY_ENVIRONMENT_DIR}/../lib/env/trt.sh"
# shellcheck source=scripts/lib/env/warmup.sh
source "${_DEPLOY_ENVIRONMENT_DIR}/../lib/env/warmup.sh"
# shellcheck source=scripts/lib/shared/gpu/environment.sh
source "${_DEPLOY_ENVIRONMENT_DIR}/../lib/shared/gpu/environment.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_DEPLOY_ENVIRONMENT_DIR}/../lib/shared/log.sh"

# _deploy_python_cache_environment: Export Python and model cache locations.
_deploy_python_cache_environment() {
  local root_dir="$1"

  export PIP_CACHE_DIR="${root_dir}/.pip_cache"
  export HF_HOME="${root_dir}/.hf"
  export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
  export HF_HUB_DISABLE_TELEMETRY=1
  export HF_HUB_ENABLE_HF_TRANSFER=0
}

# _deploy_engine_cache_environment: Export engine compilation cache locations.
_deploy_engine_cache_environment() {
  local root_dir="$1"

  export VLLM_CACHE_DIR="${root_dir}/.vllm_cache"
  export TORCHINDUCTOR_CACHE_DIR="${root_dir}/.torch_inductor"
  export TRITON_CACHE_DIR="${root_dir}/.triton"
  export FLASHINFER_CACHE_DIR="${root_dir}/.flashinfer"
}

# _deploy_quantization_environment: Export GPU-specific quantization values.
_deploy_quantization_environment() {
  local force_rebuild

  cfg_assign_value force_rebuild QUANT_FORCE_REBUILD "${CFG_QUANT_DEFAULT_FORCE_REBUILD}"
  if [[ ! ${force_rebuild} =~ ${CFG_PATTERN_BINARY_FLAG} ]]; then
    log_write "[quant] QUANT_FORCE_REBUILD must be 0 or 1"
    return 1
  fi
  QUANT_FORCE_REBUILD="${force_rebuild}"
  export QUANT_FORCE_REBUILD
  case "${GPU_SM_ARCH:?GPU_SM_ARCH is required}" in
    sm80 | sm86) cfg_export_default KV_DTYPE "auto" ;;
    sm89 | sm90 | sm100 | sm103 | sm120) cfg_export_default KV_DTYPE "fp8" ;;
    *)
      log_write "[quant] Unsupported GPU architecture: ${GPU_SM_ARCH}"
      return 1
      ;;
  esac
}

# _deploy_engine_environment: Export engine-specific runtime values.
_deploy_engine_environment() {
  case "${INFERENCE_ENGINE:?INFERENCE_ENGINE is required}" in
    trt)
      trt_initialize_environment
      ;;
    vllm)
      cfg_export_default ENFORCE_EAGER "0"
      export CUDA_MODULE_LOADING="LAZY"
      export VLLM_WORKER_MULTIPROC_METHOD="spawn"
      ;;
    *)
      return 2
      ;;
  esac
}

# deploy_initialize_environment: Initialize all host deployment paths and defaults.
# Globals:
#   INFERENCE_ENGINE
#   MODEL
#   REQUESTED_QUANTIZATION
#   RUNTIME_QUANTIZATION
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes validation failures to standard error.
# Returns:
#   0 after exporting a complete environment, non-zero otherwise.
deploy_initialize_environment() {
  local root_dir="$1"

  [[ -n ${MODEL-} ]] || return 2
  export ROOT_DIR="${root_dir}"
  export MODEL REQUESTED_QUANTIZATION RUNTIME_QUANTIZATION
  runtime_initialize_paths "${root_dir}" || return 1
  _deploy_python_cache_environment "${root_dir}"
  _deploy_engine_cache_environment "${root_dir}"
  gpu_detect || return 1
  gpu_apply_environment || return 1
  _deploy_quantization_environment || return 1
  _deploy_engine_environment || return 1
  warmup_initialize_environment "${root_dir}"
}
