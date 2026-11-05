#!/usr/bin/env bash
#
# Initialize validated warmup runtime values.
# Runtime: Bash 3.2+, macOS and Linux.

_WARMUP_ENV_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_WARMUP_ENV_FOLDER}/../../config/defaults.sh"
# shellcheck source=scripts/config/values/deployment.sh
source "${_WARMUP_ENV_FOLDER}/../../config/values/deployment.sh"
# shellcheck source=scripts/config/values/runtime.sh
source "${_WARMUP_ENV_FOLDER}/../../config/values/runtime.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_WARMUP_ENV_FOLDER}/../foundation/log.sh"

# _warmup_positive_integer: Validate and export one positive integer.
_warmup_positive_integer() {
  local variable_name="$1"
  local default_value="$2"
  local value="${!variable_name-}"

  if [[ -z ${value} ]]; then
    value="${default_value}"
  fi
  if [[ ! ${value} =~ ^[1-9][0-9]*$ ]]; then
    log_write "[warmup] ${variable_name} must be a positive integer"
    return 1
  fi
  printf -v "${variable_name}" '%s' "${value}"
  export "${variable_name?}"
}

# warmup_initialize_environment: Export warmup paths, timeouts, and retries.
# Globals:
#   WARMUP_READINESS_SCRIPT
#   WARMUP_HEALTH_POLL_INTERVAL_SECONDS
#   WARMUP_LOCK_FILE
#   WARMUP_LOG_FILE
#   WARMUP_RETRIES
#   WARMUP_RUN_DELAY_SECONDS
#   WARMUP_TIMEOUT_SECONDS
# Arguments:
#   $1: Repository root.
# Outputs:
#   Writes validation failures to standard error.
# Returns:
#   0 for valid values, non-zero otherwise.
warmup_initialize_environment() {
  local root_folder="$1"

  config_export_default \
    WARMUP_HEALTH_POLL_INTERVAL_SECONDS \
    "${WARMUP_HEALTH_POLL_SECONDS}"
  config_export_default WARMUP_RUN_DELAY_SECONDS "${WARMUP_DELAY_SECONDS_DEFAULT}"
  config_export_default WARMUP_LOG_FILE "${root_folder}/${RUNTIME_WARMUP_LOG_FILE}"
  config_export_default WARMUP_LOCK_FILE "${root_folder}/${RUNTIME_WARMUP_LOCK_FILE}"
  WARMUP_READINESS_SCRIPT="${root_folder}/scripts/readiness.sh"
  export WARMUP_READINESS_SCRIPT
  _warmup_positive_integer WARMUP_TIMEOUT_SECONDS "${WARMUP_TIMEOUT_SECONDS_DEFAULT}"
  _warmup_positive_integer WARMUP_RETRIES "${WARMUP_RETRIES_DEFAULT}"
}
