#!/usr/bin/env bash
#
# Initialize repository-owned runtime directories.
# Runtime: Bash 3.2+, macOS and Linux.

_RUNTIME_ENV_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_RUNTIME_ENV_FOLDER}/../../config/defaults.sh"
# shellcheck source=scripts/config/values/runtime.sh
source "${_RUNTIME_ENV_FOLDER}/../../config/values/runtime.sh"

# runtime_initialize_paths: Create and export runtime directories.
# Globals:
#   LOG_FOLDER
#   RUN_FOLDER
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 after creating both directories, non-zero on filesystem failure.
runtime_initialize_paths() {
  local root_folder="$1"
  local log_folder
  local run_folder

  config_assign_value log_folder LOG_FOLDER "${root_folder}/${RUNTIME_LOG_FOLDER}"
  config_assign_value run_folder RUN_FOLDER "${root_folder}/${RUNTIME_RUN_FOLDER}"
  LOG_FOLDER="${log_folder}"
  RUN_FOLDER="${run_folder}"
  export LOG_FOLDER RUN_FOLDER
  mkdir -p -- "${log_folder}" "${run_folder}"
}
