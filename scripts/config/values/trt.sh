#!/usr/bin/env bash
#
# Define TensorRT and Model Optimizer integration values.
# Runtime: Bash 3.2+, Linux.

# shellcheck disable=SC2034 # lint:justify -- reason: sourced configuration exports variables consumed by parent scripts -- ticket: N/A
[[ -n ${_CFG_TRT_READY:-} ]] && return 0
readonly _CFG_TRT_READY=1

readonly CFG_TRT_VERSION="1.3.0rc20"
readonly CFG_TRT_MIN_CUDA_VERSION="13.1"
readonly CFG_MODELOPT_TAG="0.45.0"
readonly CFG_MODELOPT_PACKAGE_VERSION="0.45.0"
readonly CFG_MODELOPT_COMMIT="ec87a82927d003986d44fb7f4fa8b3d10c31b095"
readonly CFG_MODELOPT_REPO_URL="https://github.com/NVIDIA/Model-Optimizer.git"
readonly CFG_MODELOPT_REPO_DIR_REL=".modelopt-repo"

readonly CFG_MPI_VERSION_PIN="4.1.6-7ubuntu2"
readonly CFG_TRT_FP8_SM_ARCHS="sm89 sm90"
readonly CFG_TRT_NVFP4_SM_ARCHS="sm100 sm103 sm120"
readonly CFG_TRT_DEFAULT_DTYPE="auto"
readonly CFG_TRT_DEFAULT_AWQ_BLOCK_SIZE="128"
readonly CFG_TRT_DEFAULT_CALIBRATION_DATASET="cnn_dailymail"
readonly CFG_TRT_DEFAULT_CALIBRATION_SAMPLES="64"
readonly CFG_TRT_DEFAULT_CALIBRATION_SEQUENCE_LENGTH="512"
readonly CFG_TRT_DEFAULT_CALIBRATION_MEMORY_FRACTION="0.8"
readonly CFG_TRT_DEFAULT_SEQUENTIAL_DEVICE_MAP="0"
readonly CFG_TRT_DEFAULT_MAX_BATCH_SIZE="64"
readonly CFG_TRT_DEFAULT_KV_CACHE_FP8="fp8"
readonly CFG_TRT_DEFAULT_KV_CACHE_NONE="none"
readonly CFG_TRT_QUANT_LOG_LEVEL="error"
readonly CFG_TRT_TQDM_DISABLE_DEFAULT="1"
readonly CFG_TRT_DISABLE_HF_PROGRESS_BARS="1"
