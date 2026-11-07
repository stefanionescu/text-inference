#!/usr/bin/env bash
#
# Create and validate managed Python virtual environments.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns host Python package installation and venv creation.

_VENV_DEPS_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/deployment.sh
source "${_VENV_DEPS_FOLDER}/../../config/values/deployment.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_VENV_DEPS_FOLDER}/../foundation/log.sh"

# _venv_python_version - Print one interpreter's major and minor version.
_venv_python_version() {
  local python_bin="$1"
  local version_output
  local version

  version_output="$("${python_bin}" --version 2>&1)" || return 1
  version="${version_output#Python }"
  version="${version%.*}"
  printf '%s\n' "${version}"
}

# _venv_install_python - Install the configured Python interpreter with apt.
# Globals:
#   DEPLOY_PYTHON_VERSION
#   EUID
# Arguments:
#   None.
# Outputs:
#   Writes package installation progress and failures to standard error.
# Returns:
#   0 after installation, non-zero on package-manager failure.
_venv_install_python() {
  local -a apt_command=(apt-get)
  local -a install_command=(env DEBIAN_FRONTEND=noninteractive apt-get)
  local package_name="python${DEPLOY_PYTHON_VERSION}"

  command -v apt-get >/dev/null 2>&1 || return 1
  if ((EUID != 0)); then
    apt_command=(sudo -n apt-get)
    install_command=(sudo -n env DEBIAN_FRONTEND=noninteractive apt-get)
  fi
  "${apt_command[@]}" update -y || return 1
  "${install_command[@]}" install -y \
    --no-install-recommends \
    "${package_name}" \
    "${package_name}-dev" \
    "${package_name}-venv"
}

# venv_prepare - Create or validate a managed Python environment.
# Globals:
#   DEPLOY_PYTHON_VERSION
# Arguments:
#   $1: Virtual environment path below the repository root.
# Outputs:
#   Writes creation and validation failures to standard error.
# Returns:
#   0 for a valid environment, non-zero otherwise.
venv_prepare() {
  local venv_path="$1"
  local python_bin="${venv_path}/bin/python"
  local bootstrap_python="python${DEPLOY_PYTHON_VERSION}"
  local current_version

  if [[ -d ${venv_path} ]]; then
    [[ -x ${python_bin} ]] || return 1
    current_version="$(_venv_python_version "${python_bin}")" || return 1
    [[ ${current_version} == "${DEPLOY_PYTHON_VERSION}" ]] || return 1
    return 0
  fi
  if ! command -v "${bootstrap_python}" >/dev/null 2>&1; then
    log_write "[python] Installing Python ${DEPLOY_PYTHON_VERSION}"
    _venv_install_python || return 1
  fi
  current_version="$(_venv_python_version "${bootstrap_python}")" || return 1
  if [[ ${current_version} != "${DEPLOY_PYTHON_VERSION}" ]]; then
    log_write "[python] Python ${DEPLOY_PYTHON_VERSION} is required"
    return 1
  fi
  log_write "[venv] Creating ${venv_path}"
  "${bootstrap_python}" -m venv "${venv_path}"
}
