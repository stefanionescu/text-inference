#!/usr/bin/env bash
#
# Resolve and validate TensorRT model checkpoint artifacts.
# Runtime: Bash 3.2+, Linux.

# trt_checkpoint_path: Print the repository-owned ModelOpt export path.
# Globals:
#   TRT_CACHE_FOLDER
# Arguments:
#   $1: Source model identifier.
#   $2: Quantization format.
# Outputs:
#   Writes the checkpoint directory to standard output.
# Returns:
#   0 after writing the path.
trt_checkpoint_path() {
  local source_model="$1"
  local quantization_format="$2"

  printf '%s\n' \
    "${TRT_CACHE_FOLDER:?TRT_CACHE_FOLDER is required}/${source_model##*/}-${quantization_format}-ckpt"
}

# trt_validate_checkpoint: Validate one TensorRT Hugging Face checkpoint.
# Globals:
#   ROOT_FOLDER
#   VENV_FOLDER
# Arguments:
#   $1: Checkpoint directory.
#   $2: Quantization format.
# Outputs:
#   Writes validation diagnostics to the caller streams.
# Returns:
#   The repository validation command status.
trt_validate_checkpoint() {
  local checkpoint_folder="$1"
  local quantization_format="$2"
  local python_bin="${VENV_FOLDER:?VENV_FOLDER is required}/bin/python"

  PYTHONPATH="${ROOT_FOLDER:?ROOT_FOLDER is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.quantization.checkpoint \
    --checkpoint-dir "${checkpoint_folder}" \
    --engine trt \
    --format "${quantization_format}"
}
