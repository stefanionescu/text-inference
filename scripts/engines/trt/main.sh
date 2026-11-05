#!/usr/bin/env bash
#
# Prepare the exact checkpoint consumed by the TensorRT backend.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the TensorRT checkpoint preparation workflow.

_TRT_MAIN_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/engines/trt/artifacts.sh
source "${_TRT_MAIN_FOLDER}/artifacts.sh"
# shellcheck source=scripts/engines/trt/detection.sh
source "${_TRT_MAIN_FOLDER}/detection.sh"
# shellcheck source=scripts/engines/trt/publishing.sh
source "${_TRT_MAIN_FOLDER}/publishing.sh"
# shellcheck source=scripts/engines/trt/quantization.sh
source "${_TRT_MAIN_FOLDER}/quantization.sh"
# shellcheck source=scripts/lib/env/trt.sh
source "${_TRT_MAIN_FOLDER}/../../lib/env/trt.sh"
# shellcheck source=scripts/lib/foundation/gpu/environment.sh
source "${_TRT_MAIN_FOLDER}/../../lib/foundation/gpu/environment.sh"
# shellcheck source=scripts/engines/checkpoint.sh
source "${_TRT_MAIN_FOLDER}/../checkpoint.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_TRT_MAIN_FOLDER}/../../lib/foundation/log.sh"

# _trt_publish_requested: Publish only a validated local export when requested.
_trt_publish_requested() {
  if [[ ${PUSH_REQUESTED:?PUSH_REQUESTED is required} == "0" ]]; then
    return 0
  fi
  if [[ -z ${EXPORT_PROVENANCE-} ]]; then
    log_write "[trt] --push requires a repository-provenanced local export"
    return 1
  fi
  trt_publish_checkpoint "${EXPORT_PROVENANCE}" "${RUNTIME_QUANTIZATION-}"
}

# trt_prepare_checkpoint: Resolve, optionally export, validate, and publish.
# Globals:
#   Deployment model, quantization, GPU, and publishing state.
# Arguments:
#   None.
# Outputs:
#   Writes checkpoint preparation diagnostics to standard error.
# Returns:
#   0 for a validated checkpoint, non-zero otherwise.
trt_prepare_checkpoint() {
  local source_model="${SOURCE_MODEL:?SOURCE_MODEL is required}"
  local checkpoint_action="${CHECKPOINT_ACTION:?CHECKPOINT_ACTION is required}"
  local source_folder
  local detected_format
  local checkpoint_folder

  gpu_detect || return 1
  source_folder="$(checkpoint_source_path "${source_model}")" || return 1
  detected_format="$(checkpoint_quantization_format "${source_folder}")" || return 1
  if [[ ${detected_format} != "${RUNTIME_QUANTIZATION-}" && ${checkpoint_action} == "unchanged" ]]; then
    log_write "[quant] Source metadata changed after inspection"
    return 1
  fi
  EXPORT_PROVENANCE=""
  case "${checkpoint_action}" in
    unchanged)
      checkpoint_folder="${source_folder}"
      if [[ -n ${detected_format} ]]; then
        trt_validate_format "${detected_format}" "${GPU_SM_ARCH}" || return 1
        trt_validate_checkpoint "${checkpoint_folder}" "${detected_format}" || return 1
      fi
      ;;
    export)
      [[ -n ${REQUESTED_QUANTIZATION-} && -z ${detected_format} ]] || return 1
      trt_validate_format "${REQUESTED_QUANTIZATION}" "${GPU_SM_ARCH}" || return 1
      checkpoint_folder="$(trt_checkpoint_path "${source_model}" "${REQUESTED_QUANTIZATION}")" || return 1
      trt_export_checkpoint \
        "${source_model}" "${source_folder}" "${checkpoint_folder}" \
        "${REQUESTED_QUANTIZATION}" || return 1
      trt_validate_checkpoint "${checkpoint_folder}" "${REQUESTED_QUANTIZATION}" || return 1
      EXPORT_PROVENANCE="${checkpoint_folder}"
      ;;
    online) return 2 ;;
    *) return 2 ;;
  esac
  MODEL="${checkpoint_folder}"
  RESOLVED_CHECKPOINT="${checkpoint_folder}"
  export EXPORT_PROVENANCE MODEL RESOLVED_CHECKPOINT RUNTIME_QUANTIZATION
  _trt_publish_requested
}
