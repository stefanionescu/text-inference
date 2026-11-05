#!/usr/bin/env bash
#
# Initialize and validate TensorRT host environment values.
# Runtime: Bash 3.2+, Linux.

_TRT_ENV_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_TRT_ENV_DIR}/../../config/defaults.sh"
# shellcheck source=scripts/config/patterns.sh
source "${_TRT_ENV_DIR}/../../config/patterns.sh"
# shellcheck source=scripts/config/values/trt.sh
source "${_TRT_ENV_DIR}/../../config/values/trt.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_TRT_ENV_DIR}/../shared/log.sh"

# trt_initialize_environment: Export TensorRT and Model Optimizer paths.
# Globals:
#   MODELOPT_REPO_DIR
#   MPI_VERSION_PIN
#   ROOT_DIR
#   TRT_CACHE_DIR
# Arguments:
#   None.
# Outputs:
#   None.
# Returns:
#   0 after exporting defaults.
trt_initialize_environment() {
  local root_dir="${ROOT_DIR:?ROOT_DIR is required}"

  export MPI_VERSION_PIN="${CFG_MPI_VERSION_PIN}"
  export MODELOPT_REPO_DIR="${root_dir}/${CFG_MODELOPT_REPO_DIR_REL}"
  export TRT_CACHE_DIR="${root_dir}/.trt_cache"
  cfg_export_default TRT_AWQ_BLOCK_SIZE "${CFG_TRT_DEFAULT_AWQ_BLOCK_SIZE}"
  cfg_export_default TRT_CALIBRATION_DATASET "${CFG_TRT_DEFAULT_CALIBRATION_DATASET}"
  cfg_export_default TRT_CALIBRATION_SAMPLES "${CFG_TRT_DEFAULT_CALIBRATION_SAMPLES}"
  cfg_export_default TRT_CALIBRATION_SEQUENCE_LENGTH "${CFG_TRT_DEFAULT_CALIBRATION_SEQUENCE_LENGTH}"
  cfg_export_default \
    TRT_CALIBRATION_MEMORY_FRACTION \
    "${CFG_TRT_DEFAULT_CALIBRATION_MEMORY_FRACTION}"
  cfg_export_default \
    TRT_SEQUENTIAL_DEVICE_MAP \
    "${CFG_TRT_DEFAULT_SEQUENTIAL_DEVICE_MAP}"
}

# trt_validate_calibration: Validate Model Optimizer calibration settings.
# Globals:
#   TRT_AWQ_BLOCK_SIZE
#   TRT_CALIBRATION_MEMORY_FRACTION
#   TRT_CALIBRATION_SEQUENCE_LENGTH
#   TRT_CALIBRATION_SAMPLES
#   TRT_SEQUENTIAL_DEVICE_MAP
# Arguments:
#   None.
# Outputs:
#   Writes validation failures to standard error.
# Returns:
#   0 for valid settings, non-zero otherwise.
trt_validate_calibration() {
  if [[ ! ${TRT_AWQ_BLOCK_SIZE:?TRT_AWQ_BLOCK_SIZE is required} =~ ${CFG_PATTERN_POSITIVE_INT} ]]; then
    log_write "[trt] TRT_AWQ_BLOCK_SIZE must be a positive integer"
    return 1
  fi
  if [[ ! ${TRT_CALIBRATION_SAMPLES:?TRT_CALIBRATION_SAMPLES is required} =~ ${CFG_PATTERN_POSITIVE_INT} ]]; then
    log_write "[trt] TRT_CALIBRATION_SAMPLES must be a positive integer"
    return 1
  fi
  if [[ ! ${TRT_CALIBRATION_SEQUENCE_LENGTH:?TRT_CALIBRATION_SEQUENCE_LENGTH is required} =~ ${CFG_PATTERN_POSITIVE_INT} ]]; then
    log_write "[trt] TRT_CALIBRATION_SEQUENCE_LENGTH must be a positive integer"
    return 1
  fi
  if [[ ! ${TRT_CALIBRATION_MEMORY_FRACTION:?TRT_CALIBRATION_MEMORY_FRACTION is required} =~ ${CFG_PATTERN_POSITIVE_FRACTION} ]]; then
    log_write "[trt] TRT_CALIBRATION_MEMORY_FRACTION must be greater than 0 and at most 1"
    return 1
  fi
  if [[ ! ${TRT_SEQUENTIAL_DEVICE_MAP:?TRT_SEQUENTIAL_DEVICE_MAP is required} =~ ${CFG_PATTERN_BINARY_FLAG} ]]; then
    log_write "[trt] TRT_SEQUENTIAL_DEVICE_MAP must be 0 or 1"
    return 1
  fi
}

# trt_validate_format: Validate one Model Optimizer format for the GPU.
# Globals:
#   CFG_TRT_FP8_SM_ARCHS
#   CFG_TRT_NVFP4_SM_ARCHS
# Arguments:
#   $1: Quantization format.
#   $2: GPU architecture.
# Outputs:
#   Writes unsupported combinations to standard error.
# Returns:
#   0 for a supported format, non-zero otherwise.
trt_validate_format() {
  local quantization_format="$1"
  local architecture="$2"

  case "${quantization_format}" in
    int4_awq)
      return 0
      ;;
    fp8)
      [[ " ${CFG_TRT_FP8_SM_ARCHS} " == *" ${architecture} "* ]] && return 0
      log_write "[trt] FP8 requires one of: ${CFG_TRT_FP8_SM_ARCHS}"
      return 1
      ;;
    nvfp4)
      [[ " ${CFG_TRT_NVFP4_SM_ARCHS} " == *" ${architecture} "* ]] && return 0
      log_write "[trt] NVFP4 requires one of: ${CFG_TRT_NVFP4_SM_ARCHS}"
      return 1
      ;;
    *)
      log_write "[trt] Unsupported TensorRT format: ${quantization_format}"
      return 1
      ;;
  esac
}
