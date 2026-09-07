#!/usr/bin/env bash
#
# Prepare the exact checkpoint consumed by the vLLM backend.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the vLLM checkpoint preparation workflow.

_VLLM_ENGINE_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/engines/checkpoint.sh
source "${_VLLM_ENGINE_DIR}/checkpoint.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_VLLM_ENGINE_DIR}/../lib/shared/log.sh"

# _vllm_select_online - Select one raw checkpoint for online FP8.
_vllm_select_online() {
  [[ ${REQUESTED_QUANTIZATION-} == "fp8" && -z $2 ]] || return 1
  log_write "[quant] vLLM will apply online FP8 quantization"
  MODEL="$1"
}

# _vllm_export_checkpoint - Export one raw source to compressed-tensors.
_vllm_export_checkpoint() {
  local source_model="$1"
  local detected_format="$2"
  local checkpoint_dir="${ROOT_DIR:?ROOT_DIR is required}/.compressed-tensors/model"
  local quantizer_python="${QUANT_VENV_DIR:?QUANT_VENV_DIR is required}/bin/python"

  [[ ${REQUESTED_QUANTIZATION-} == "compressed-tensors" && -z ${detected_format} ]] || return 1
  PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${quantizer_python}" -m src.quantization.vllm.quantize \
    --model "${source_model}" --out "${checkpoint_dir}" || return 1
  MODEL="${checkpoint_dir}"
  EXPORT_PROVENANCE="${checkpoint_dir}"
}

# _vllm_apply_checkpoint_action - Select or export the requested checkpoint.
_vllm_apply_checkpoint_action() {
  local source_model="$1"
  local source_dir="$2"
  local detected_format="$3"

  EXPORT_PROVENANCE=""
  case "${CHECKPOINT_ACTION:?CHECKPOINT_ACTION is required}" in
    unchanged)
      MODEL="${source_dir}"
      ;;
    online)
      _vllm_select_online "${source_dir}" "${detected_format}"
      ;;
    export)
      _vllm_export_checkpoint "${source_model}" "${detected_format}"
      ;;
    *) return 2 ;;
  esac
}

# _vllm_publish_requested - Publish only a validated local export when requested.
_vllm_publish_requested() {
  if [[ ${PUSH_REQUESTED:?PUSH_REQUESTED is required} == "0" ]]; then
    return 0
  fi
  if [[ -z ${EXPORT_PROVENANCE-} ]]; then
    log_write "[vllm] --push requires a repository-provenanced local export"
    return 1
  fi
  vllm_publish_checkpoint "${EXPORT_PROVENANCE}"
}

# vllm_publish_checkpoint - Upload one local compressed-tensors checkpoint.
# Globals:
#   HF_PUSH_PRIVATE, HF_PUSH_REPO_ID, ROOT_DIR, VENV_DIR.
# Arguments:
#   $1: Provenanced local checkpoint directory.
# Outputs:
#   Writes upload output to the caller streams.
# Returns:
#   0 after upload, non-zero otherwise.
vllm_publish_checkpoint() {
  local checkpoint_dir="$1"
  local python_bin="${VENV_DIR:?VENV_DIR is required}/bin/python"
  local -a arguments=(
    --checkpoint-dir "${checkpoint_dir}"
    --repo-id "${HF_PUSH_REPO_ID:?HF_PUSH_REPO_ID is required}"
  )

  [[ -d ${checkpoint_dir} && -x ${python_bin} ]] || return 1
  [[ ${HF_PUSH_PRIVATE:?HF_PUSH_PRIVATE is required} != "1" ]] || arguments+=(--private)
  PYTHONPATH="${ROOT_DIR:?ROOT_DIR is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.hf.vllm "${arguments[@]}"
}

# vllm_prepare_checkpoint - Resolve, optionally export, and publish a checkpoint.
# Globals:
#   Deployment model, quantization, environment, and publishing state.
# Arguments:
#   None.
# Outputs:
#   Writes checkpoint preparation diagnostics to standard error.
# Returns:
#   0 for a selected checkpoint, non-zero otherwise.
vllm_prepare_checkpoint() {
  local source_model="${SOURCE_MODEL:?SOURCE_MODEL is required}"
  local checkpoint_action="${CHECKPOINT_ACTION:?CHECKPOINT_ACTION is required}"
  local source_dir
  local detected_format

  source_dir="$(checkpoint_source_path "${source_model}")" || return 1
  detected_format="$(checkpoint_quantization_format "${source_dir}")" || return 1
  if [[ ${detected_format} != "${RUNTIME_QUANTIZATION-}" && ${checkpoint_action} == "unchanged" ]]; then
    log_write "[quant] Source metadata changed after inspection"
    return 1
  fi
  _vllm_apply_checkpoint_action "${source_model}" "${source_dir}" "${detected_format}" || return 1
  RESOLVED_CHECKPOINT="${MODEL}"
  export EXPORT_PROVENANCE MODEL RESOLVED_CHECKPOINT RUNTIME_QUANTIZATION
  _vllm_publish_requested
}
