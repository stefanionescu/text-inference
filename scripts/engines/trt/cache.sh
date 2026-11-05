#!/usr/bin/env bash
#
# Evaluate and record TensorRT ModelOpt checkpoint provenance.
# Runtime: Bash 3.2+, Linux.

_TRT_CACHE_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/trt.sh
source "${_TRT_CACHE_DIR}/../../config/values/trt.sh"
# shellcheck source=scripts/engines/trt/detection.sh
source "${_TRT_CACHE_DIR}/detection.sh"

# trt_cache_action: Print whether a ModelOpt checkpoint can be reused.
# Globals:
#   ModelOpt calibration and repository runtime variables.
# Arguments:
#   $1: Source model identifier.
#   $2: Source checkpoint directory.
#   $3: Export checkpoint directory.
#   $4: Quantization format.
#   $5: KV-cache format.
# Outputs:
#   Writes reuse or rebuild to standard output.
# Returns:
#   The repository cache policy command status.
trt_cache_action() {
  local source_model="$1"
  local source_dir="$2"
  local checkpoint_dir="$3"
  local quantization_format="$4"
  local kv_cache_format="$5"
  local python_bin="${QUANT_VENV_DIR:?QUANT_VENV_DIR is required}/bin/python"
  local -a arguments=(
    --source-model "${source_model}" --source-dir "${source_dir}"
    --source-revision "${SOURCE_REVISION:?SOURCE_REVISION is required}"
    --checkpoint-dir "${checkpoint_dir}" --format "${quantization_format}"
    --calibration-dataset "${TRT_CALIBRATION_DATASET:?TRT_CALIBRATION_DATASET is required}"
    --calibration-samples "${TRT_CALIBRATION_SAMPLES:?TRT_CALIBRATION_SAMPLES is required}"
    --calibration-sequence-length "${TRT_CALIBRATION_SEQUENCE_LENGTH:?TRT_CALIBRATION_SEQUENCE_LENGTH is required}"
    --awq-block-size "${TRT_AWQ_BLOCK_SIZE:?TRT_AWQ_BLOCK_SIZE is required}"
    --kv-cache-format "${kv_cache_format}"
    --gpu-max-mem-percentage "${TRT_CALIBRATION_MEMORY_FRACTION:?TRT_CALIBRATION_MEMORY_FRACTION is required}"
    --sequential-device-map "${TRT_SEQUENTIAL_DEVICE_MAP:?TRT_SEQUENTIAL_DEVICE_MAP is required}"
    --modelopt-repository "${MODELOPT_REPO_DIR:?MODELOPT_REPO_DIR is required}"
  )

  [[ ${QUANT_FORCE_REBUILD:?QUANT_FORCE_REBUILD is required} == "0" ]] || arguments+=(--force-rebuild)
  PYTHONPATH="${ROOT_DIR:?ROOT_DIR is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.quantization.trt cache "${arguments[@]}"
}

# trt_finalize_checkpoint: Validate an export and persist exact provenance.
# Globals:
#   ModelOpt, GPU, and repository runtime variables.
# Arguments:
#   $1: Source model identifier.
#   $2: Source checkpoint directory.
#   $3: Export checkpoint directory.
#   $4: Quantization format.
#   $5: KV-cache format.
# Outputs:
#   Writes finalization diagnostics to the caller streams.
# Returns:
#   The repository finalization command status.
trt_finalize_checkpoint() {
  local source_model="$1"
  local source_dir="$2"
  local checkpoint_dir="$3"
  local quantization_format="$4"
  local kv_cache_format="$5"
  local python_bin="${QUANT_VENV_DIR:?QUANT_VENV_DIR is required}/bin/python"
  local cuda_version

  cuda_version="$(trt_cuda_version)" || return 1
  PYTHONPATH="${ROOT_DIR:?ROOT_DIR is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.quantization.trt finalize \
    --source-model "${source_model}" --source-dir "${source_dir}" \
    --source-revision "${SOURCE_REVISION:?SOURCE_REVISION is required}" \
    --checkpoint-dir "${checkpoint_dir}" --format "${quantization_format}" \
    --calibration-dataset "${TRT_CALIBRATION_DATASET:?TRT_CALIBRATION_DATASET is required}" \
    --calibration-samples "${TRT_CALIBRATION_SAMPLES:?TRT_CALIBRATION_SAMPLES is required}" \
    --calibration-sequence-length "${TRT_CALIBRATION_SEQUENCE_LENGTH:?TRT_CALIBRATION_SEQUENCE_LENGTH is required}" \
    --awq-block-size "${TRT_AWQ_BLOCK_SIZE:?TRT_AWQ_BLOCK_SIZE is required}" \
    --kv-cache-format "${kv_cache_format}" \
    --gpu-max-mem-percentage "${TRT_CALIBRATION_MEMORY_FRACTION:?TRT_CALIBRATION_MEMORY_FRACTION is required}" \
    --sequential-device-map "${TRT_SEQUENTIAL_DEVICE_MAP:?TRT_SEQUENTIAL_DEVICE_MAP is required}" \
    --modelopt-repository "${MODELOPT_REPO_DIR:?MODELOPT_REPO_DIR is required}" \
    --gpu-name "${DETECTED_GPU_NAME:?DETECTED_GPU_NAME is required}" \
    --sm-arch "${GPU_SM_ARCH:?GPU_SM_ARCH is required}" --cuda-version "${cuda_version}"
}
