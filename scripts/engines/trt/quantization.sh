#!/usr/bin/env bash
#
# Export TensorRT checkpoints with NVIDIA Model Optimizer.
# Runtime: Bash 3.2+, Linux.

_TRT_QUANTIZATION_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/trt.sh
source "${_TRT_QUANTIZATION_DIR}/../../config/values/trt.sh"
# shellcheck source=scripts/engines/trt/cache.sh
source "${_TRT_QUANTIZATION_DIR}/cache.sh"
# shellcheck source=scripts/engines/trt/modelopt.sh
source "${_TRT_QUANTIZATION_DIR}/modelopt.sh"
# shellcheck source=scripts/lib/env/trt.sh
source "${_TRT_QUANTIZATION_DIR}/../../lib/env/trt.sh"
# shellcheck source=scripts/lib/runtime/cleanup/paths.sh
source "${_TRT_QUANTIZATION_DIR}/../../lib/runtime/cleanup/paths.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_TRT_QUANTIZATION_DIR}/../../lib/shared/log.sh"

# _trt_kv_format: Print the KV-cache format for one quantization format.
_trt_kv_format() {
  case "$1" in
    int4_awq) printf 'none\n' ;;
    fp8) printf 'fp8\n' ;;
    nvfp4) printf 'nvfp4\n' ;;
    *) return 1 ;;
  esac
}

# _trt_run_quantizer: Run ModelOpt with quiet or raw dependency output.
# Globals:
#   LOGS_ENABLED and fixed TensorRT dependency logging values.
# Arguments:
#   $1: Quantizer Python executable. Remaining arguments: ModelOpt command.
# Outputs:
#   Writes ModelOpt output to the caller streams.
# Returns:
#   The ModelOpt command status.
_trt_run_quantizer() {
  local quantizer_python="$1"

  shift
  if [[ ${LOGS_ENABLED:?LOGS_ENABLED is required} == "1" ]]; then
    "${quantizer_python}" "$@"
    return
  fi
  HF_HUB_DISABLE_PROGRESS_BARS="${CFG_TRT_DISABLE_HF_PROGRESS_BARS}" \
    TQDM_DISABLE="${CFG_TRT_TQDM_DISABLE_DEFAULT}" \
    TRTLLM_LOG_LEVEL="${CFG_TRT_QUANT_LOG_LEVEL}" \
    "${quantizer_python}" "$@"
}

# trt_export_checkpoint: Reuse or create one ModelOpt checkpoint.
# Globals:
#   ModelOpt calibration, repository, and virtual environment variables.
# Arguments:
#   $1: Source model identifier.
#   $2: Source checkpoint directory.
#   $3: Export checkpoint directory.
#   $4: Quantization format.
# Outputs:
#   Writes quantization progress and failures to standard error.
# Returns:
#   0 after reuse or export, non-zero otherwise.
trt_export_checkpoint() {
  local source_model="$1"
  local source_dir="$2"
  local checkpoint_dir="$3"
  local quantization_format="$4"
  local quantizer_python="${QUANT_VENV_DIR:?QUANT_VENV_DIR is required}/bin/python"
  local quantizer_script
  local cache_action
  local kv_cache_format
  local -a arguments

  trt_validate_calibration || return 1
  kv_cache_format="$(_trt_kv_format "${quantization_format}")" || return 1
  trt_prepare_modelopt || return 1
  cache_action="$(trt_cache_action \
    "${source_model}" "${source_dir}" "${checkpoint_dir}" \
    "${quantization_format}" "${kv_cache_format}")" || return 1
  if [[ ${cache_action} == "reuse" ]]; then
    log_write "[quant] Reusing ModelOpt checkpoint: ${checkpoint_dir}"
    return 0
  fi
  quantizer_script="${MODELOPT_REPO_DIR}/examples/llm_ptq/hf_ptq.py"
  arguments=(
    "${quantizer_script}" --pyt_ckpt_path "${source_dir}" --export_path "${checkpoint_dir}"
    --trust_remote_code --qformat "${quantization_format}" --dataset "${TRT_CALIBRATION_DATASET}"
    --calib_size "${TRT_CALIBRATION_SAMPLES}" --calib_seq "${TRT_CALIBRATION_SEQUENCE_LENGTH}"
    --gpu_max_mem_percentage "${TRT_CALIBRATION_MEMORY_FRACTION}"
    --kv_cache_qformat "${kv_cache_format}"
  )
  [[ ${quantization_format} != "int4_awq" ]] || arguments+=(--awq_block_size "${TRT_AWQ_BLOCK_SIZE}")
  [[ ${TRT_SEQUENTIAL_DEVICE_MAP} != "1" ]] || arguments+=(--use_seq_device_map)
  runtime_remove_owned_path "${ROOT_DIR}" "${checkpoint_dir}" || return 1
  mkdir -p -- "${checkpoint_dir}" || return 1
  _trt_run_quantizer "${quantizer_python}" "${arguments[@]}" || return 1
  trt_finalize_checkpoint \
    "${source_model}" "${source_dir}" "${checkpoint_dir}" \
    "${quantization_format}" "${kv_cache_format}" || return 1
  log_write "[quant] Quantization complete: ${checkpoint_dir}"
}
