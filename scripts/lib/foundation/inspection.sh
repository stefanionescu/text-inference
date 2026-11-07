#!/usr/bin/env bash
#
# Resolve immutable model identity and quantization before deployment mutation.
# Runtime: Bash 3.2+, Linux.

_INSPECTION_FOUNDATION_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_INSPECTION_FOUNDATION_FOLDER}/../../config/defaults.sh"
# shellcheck source=scripts/config/values/quantization.sh
source "${_INSPECTION_FOUNDATION_FOLDER}/../../config/values/quantization.sh"
# shellcheck source=scripts/config/values/runtime.sh
source "${_INSPECTION_FOUNDATION_FOLDER}/../../config/values/runtime.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_INSPECTION_FOUNDATION_FOLDER}/log.sh"

# _inspection_run - Run the standard-library-only metadata inspector.
_inspection_run() {
  local root_folder="$1"
  local model="$2"
  local engine="$3"
  local requested_quantization="$4"
  local output_file="$5"
  local diagnostics_file="$6"
  local requested_revision
  local -a arguments

  config_assign_value requested_revision MODEL_REVISION "${QUANT_DEFAULT_MODEL_REVISION}"
  arguments=(--model "${model}" --engine "${engine}" --revision "${requested_revision}")
  [[ -z ${requested_quantization} ]] || arguments+=(--quantization "${requested_quantization}")
  PYTHONPATH="${root_folder}${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m src.quantization.inspection "${arguments[@]}" \
    >"${output_file}" 2>"${diagnostics_file}"
}

# _inspection_read_fields - Read the exact inspector TSV protocol.
_inspection_read_fields() {
  local output_file="$1"
  local key
  local value

  while IFS=$'\t' read -r key value; do
    case "${key}" in
      SOURCE_MODEL) SOURCE_MODEL="${value}" ;;
      SOURCE_REVISION) SOURCE_REVISION="${value}" ;;
      RUNTIME_QUANTIZATION) RUNTIME_QUANTIZATION="${value}" ;;
      REQUESTED_QUANTIZATION) REQUESTED_QUANTIZATION="${value}" ;;
      CHECKPOINT_ACTION) CHECKPOINT_ACTION="${value}" ;;
      *)
        log_write "[inspect] Unexpected model inspection field: ${key}"
        return 1
        ;;
    esac
  done <"${output_file}"
}

# _inspection_report - Export and report a complete inspection result.
_inspection_report() {
  if [[ -z ${SOURCE_MODEL-} || -z ${SOURCE_REVISION-} || -z ${CHECKPOINT_ACTION-} ]]; then
    log_write "[inspect] Model inspection returned incomplete identity"
    return 1
  fi
  MODEL="${SOURCE_MODEL}"
  export CHECKPOINT_ACTION MODEL REQUESTED_QUANTIZATION RUNTIME_QUANTIZATION
  export SOURCE_MODEL SOURCE_REVISION
  log_write "[inspect] Source revision: ${SOURCE_REVISION}"
  if [[ -n ${RUNTIME_QUANTIZATION} ]]; then
    log_write "[inspect] Runtime format: ${RUNTIME_QUANTIZATION}"
  else
    log_write "[inspect] Runtime format: unquantized"
  fi
}

# deployment_inspect_model - Resolve model identity and quantization before mutation.
# Globals:
#   HF_TOKEN, MODEL_REVISION, TMPDIR.
# Arguments:
#   $1: Repository root. $2: Model. $3: Engine. $4: Optional quantization.
# Outputs:
#   Writes inspection failures to standard error.
# Returns:
#   0 after exporting the resolved model fields, non-zero otherwise.
deployment_inspect_model() {
  local root_folder="$1"
  local temporary_folder="${TMPDIR-}"
  local output_file
  local diagnostics_file
  local server_log="${root_folder}/${RUNTIME_SERVER_LOG_FILE}"
  local line
  local status=0

  command -v python3 >/dev/null 2>&1 || {
    log_write "[inspect] python3 is required for early model inspection"
    return 1
  }
  [[ -n ${temporary_folder} ]] || temporary_folder="/tmp"
  output_file="$(mktemp "${temporary_folder}/yap-inspection.XXXXXX")" || return 1
  trap 'rm -f -- "${output_file}"; trap - RETURN' RETURN
  diagnostics_file="$(mktemp "${temporary_folder}/yap-inspection-log.XXXXXX")" || return 1
  trap 'rm -f -- "${output_file}" "${diagnostics_file}"; trap - RETURN' RETURN
  _inspection_run \
    "${root_folder}" "$2" "$3" "$4" "${output_file}" "${diagnostics_file}" || status=1
  while IFS= read -r line || [[ -n ${line} ]]; do
    printf '%s\n' "${line}" >>"${server_log}" || status=1
    if log_is_repository_line "${line}"; then
      log_write "${line}"
    fi
  done <"${diagnostics_file}"
  if ((status == 0)); then
    _inspection_read_fields "${output_file}" || status=1
  fi
  if ((status != 0)); then
    log_write "[inspect] Model inspection failed; detailed diagnostics: ${server_log}"
    return 1
  fi
  _inspection_report
}
