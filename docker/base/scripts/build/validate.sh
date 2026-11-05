#!/usr/bin/env bash
# Shared model validation for Docker builds.

# validate_model_revision: Require an immutable Hugging Face revision.
validate_model_revision() {
  if [[ ! ${MODEL_REVISION:?MODEL_REVISION is required} =~ ^[0-9a-fA-F]{40}$ ]]; then
    log_write "[build] ✗ MODEL_REVISION must be a 40-character Hugging Face commit SHA."
    return 1
  fi
}

# validate_models_for_engine: Validate Docker model inputs for an engine.
# Globals:
#   ROOT_FOLDER
# Arguments:
#   $1: Engine name.
#   $2: Model name or path.
#   $3: Model revision.
validate_models_for_engine() {
  local engine="$1"
  local model="$2"
  local model_revision="$3"
  local root_folder="${ROOT_FOLDER:?ROOT_FOLDER is required for model validation}"

  if ! command -v python3 >/dev/null 2>&1; then
    log_write "[build] ✗ python3 is required for model inspection"
    return 1
  fi

  PYTHONPATH="${root_folder}${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m src.quantization.inspection \
    --model "${model}" --revision "${model_revision}" --engine "${engine}" >/dev/null
}
