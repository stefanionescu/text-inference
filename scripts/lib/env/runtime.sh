#!/usr/bin/env bash
#
# Initialize repository-owned runtime directories.
# Runtime: Bash 3.2+, macOS and Linux.

_RUNTIME_ENV_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_RUNTIME_ENV_DIR}/../../config/defaults.sh"
# shellcheck source=scripts/config/values/runtime.sh
source "${_RUNTIME_ENV_DIR}/../../config/values/runtime.sh"

# runtime_initialize_paths: Create and export runtime directories.
# Globals:
#   LOG_DIR
#   RUN_DIR
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 after creating both directories, non-zero on filesystem failure.
runtime_initialize_paths() {
  local root_dir="$1"
  local log_dir
  local run_dir

  cfg_assign_value log_dir LOG_DIR "${root_dir}/${CFG_RUNTIME_LOG_DIR}"
  cfg_assign_value run_dir RUN_DIR "${root_dir}/${CFG_RUNTIME_RUN_DIR}"
  LOG_DIR="${log_dir}"
  RUN_DIR="${run_dir}"
  export LOG_DIR RUN_DIR
  mkdir -p -- "${log_dir}" "${run_dir}"
}
