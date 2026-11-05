#!/usr/bin/env bash
# shellcheck disable=SC1091 # reason: shared GPU module is installed at this container path
source "/app/scripts/lib/shared/gpu/environment.sh"
# shellcheck source=scripts/config/defaults.sh
source "/app/scripts/config/defaults.sh"

# vllm_configure_gpu: Detect the GPU and export the vLLM settings for its architecture.
vllm_configure_gpu() {
  gpu_detect
  gpu_apply_environment

  cfg_export_default ENFORCE_EAGER "0"
  CUDA_MODULE_LOADING="LAZY"
  VLLM_WORKER_MULTIPROC_METHOD="spawn"
  case "${GPU_SM_ARCH:?GPU_SM_ARCH is required}" in
    sm80 | sm86) cfg_export_default KV_DTYPE "auto" ;;
    sm89 | sm90 | sm100 | sm103 | sm120) cfg_export_default KV_DTYPE "fp8" ;;
    *)
      log_write "[vllm] ✗ Unsupported GPU architecture: ${GPU_SM_ARCH}"
      return 1
      ;;
  esac
  export CUDA_MODULE_LOADING ENFORCE_EAGER KV_DTYPE VLLM_WORKER_MULTIPROC_METHOD
}
