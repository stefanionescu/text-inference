#!/usr/bin/env bash
#
# Resolve and validate TensorRT model checkpoint artifacts.
# Runtime: Bash 3.2+, Linux.

# trt_checkpoint_path: Print the repository-owned ModelOpt export path.
# Globals:
#   TRT_CACHE_DIR
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
    "${TRT_CACHE_DIR:?TRT_CACHE_DIR is required}/${source_model##*/}-${quantization_format}-ckpt"
}

# trt_validate_checkpoint: Validate one TensorRT Hugging Face checkpoint.
# Globals:
#   ROOT_DIR
#   VENV_DIR
# Arguments:
#   $1: Checkpoint directory.
#   $2: Quantization format.
# Outputs:
#   Writes validation diagnostics to the caller streams.
# Returns:
#   The repository validation command status.
trt_validate_checkpoint() {
  local checkpoint_dir="$1"
  local quantization_format="$2"
  local python_bin="${VENV_DIR:?VENV_DIR is required}/bin/python"

  PYTHONPATH="${ROOT_DIR:?ROOT_DIR is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.quantization.checkpoint \
    --checkpoint-dir "${checkpoint_dir}" \
    --engine trt \
    --format "${quantization_format}"
}
