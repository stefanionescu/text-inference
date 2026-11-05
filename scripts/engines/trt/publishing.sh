#!/usr/bin/env bash
#
# Publish repository-exported TensorRT checkpoints to Hugging Face.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns the TensorRT Hugging Face upload integration.

# trt_publish_checkpoint: Upload one local ModelOpt checkpoint.
# Globals:
#   HF_PUSH_PRIVATE
#   HF_PUSH_REPO_ID
#   HF_TOKEN
#   VENV_FOLDER
# Arguments:
#   $1: Checkpoint directory.
#   $2: Quantization format.
# Outputs:
#   Writes upload diagnostics to the caller streams.
# Returns:
#   The repository upload command status.
trt_publish_checkpoint() {
  local checkpoint_folder="$1"
  local quantization_format="$2"
  local python_bin="${VENV_FOLDER:?VENV_FOLDER is required}/bin/python"
  local -a arguments=(
    --checkpoint-dir "${checkpoint_folder}"
    --repo-id "${HF_PUSH_REPO_ID:?HF_PUSH_REPO_ID is required}"
    --format "${quantization_format}"
  )

  [[ -n ${HF_TOKEN-} && -d ${checkpoint_folder} && -x ${python_bin} ]] || return 1
  [[ ${HF_PUSH_PRIVATE:?HF_PUSH_PRIVATE is required} != "1" ]] || arguments+=(--private)
  "${python_bin}" -m src.hf.trt "${arguments[@]}"
}
