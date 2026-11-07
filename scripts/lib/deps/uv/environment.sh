#!/usr/bin/env bash
#
# Apply locked uv environments to managed Python interpreters.
# Runtime: Bash 3.2+, Linux.

_UV_ENVIRONMENT_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/lib/deps/uv/command.sh
source "${_UV_ENVIRONMENT_FOLDER}/command.sh"
# shellcheck source=scripts/config/defaults.sh
source "${_UV_ENVIRONMENT_FOLDER}/../../../config/defaults.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_UV_ENVIRONMENT_FOLDER}/../../foundation/log.sh"

# uv_export_environment - Export deterministic uv install settings.
# Globals:
#   FLASHINFER_ENABLE_AOT
#   UV_LINK_MODE
#   UV_NO_PROGRESS
#   UV_PYTHON_DOWNLOADS
# Arguments:
#   None.
# Outputs:
#   None.
# Returns:
#   0 after exporting the settings.
uv_export_environment() {
  config_export_default UV_NO_PROGRESS "1"
  config_export_default UV_PYTHON_DOWNLOADS "never"
  config_export_default UV_LINK_MODE "copy"
  config_export_default FLASHINFER_ENABLE_AOT "1"
}

# uv_apply_lock - Apply locked extras to one virtual environment.
# Globals:
#   ROOT_FOLDER
# Arguments:
#   $1: Virtual environment path.
#   Remaining arguments: uv sync selectors.
# Outputs:
#   Writes uv failures to standard error.
# Returns:
#   The uv sync status.
uv_apply_lock() {
  local venv_folder="$1"
  local python_bin="${venv_folder}/bin/python"
  local root_folder="${ROOT_FOLDER:?ROOT_FOLDER is required}"

  shift
  [[ -x ${python_bin} ]] || return 1
  (
    cd -- "${root_folder}" || exit 1
    UV_PROJECT_ENVIRONMENT="${venv_folder}" uv_run \
      sync \
      --frozen \
      --no-dev \
      --no-install-project \
      --python "${python_bin}" \
      --no-python-downloads \
      "$@"
  )
}

# uv_install_packages - Install special packages into the runtime environment.
# Globals:
#   VENV_FOLDER
# Arguments:
#   uv pip install arguments.
# Outputs:
#   Writes uv failures to standard error.
# Returns:
#   The uv pip status.
uv_install_packages() {
  local python_bin="${VENV_FOLDER:?VENV_FOLDER is required}/bin/python"

  [[ -x ${python_bin} ]] || return 1
  uv_run pip install --python "${python_bin}" "$@"
}
