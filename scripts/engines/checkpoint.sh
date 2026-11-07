#!/usr/bin/env bash
#
# Resolve source checkpoints and detect their declared quantization format.
# Runtime: Bash 3.2+, Linux.

# checkpoint_source_path - Acquire and print a requested source checkpoint path.
# Globals:
#   SOURCE_REVISION
#   ROOT_FOLDER
#   VENV_FOLDER
# Arguments:
#   $1: Model repository identifier or local path.
# Outputs:
#   Writes the resolved source directory to standard output.
# Returns:
#   The source acquisition command status.
checkpoint_source_path() {
  local source_model="$1"
  local python_bin="${VENV_FOLDER:?VENV_FOLDER is required}/bin/python"

  PYTHONPATH="${ROOT_FOLDER:?ROOT_FOLDER is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.quantization.source \
    --model "${source_model}" \
    --revision "${SOURCE_REVISION:?SOURCE_REVISION is required}"
}

# checkpoint_quantization_format - Print a checkpoint's declared format.
# Globals:
#   ROOT_FOLDER
#   VENV_FOLDER
# Arguments:
#   $1: Checkpoint directory.
# Outputs:
#   Writes the detected format to standard output.
# Returns:
#   The repository detection command status.
checkpoint_quantization_format() {
  local checkpoint_folder="$1"
  local python_bin="${VENV_FOLDER:?VENV_FOLDER is required}/bin/python"

  PYTHONPATH="${ROOT_FOLDER:?ROOT_FOLDER is required}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m src.quantization.detection "${checkpoint_folder}"
}
