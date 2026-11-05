#!/usr/bin/env bash
#
# Install TensorRT host MPI dependencies.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns privileged host package installation for TensorRT.

_TRT_SYSTEM_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/deployment.sh
source "${_TRT_SYSTEM_FOLDER}/../../../config/values/deployment.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_TRT_SYSTEM_FOLDER}/../../foundation/log.sh"

# _trt_install_mpi: Install the pinned MPI development packages.
# Globals:
#   DEPLOY_PYTHON_VERSION
#   EUID
#   MPI_VERSION_PIN
# Arguments:
#   None.
# Outputs:
#   Writes package-manager output to the caller streams.
# Returns:
#   0 after holding installed packages, non-zero on package-manager failure.
_trt_install_mpi() {
  local -a apt_command=(apt-get)
  local -a install_command=(env DEBIAN_FRONTEND=noninteractive apt-get)
  local -a mark_command=(apt-mark)
  local mpi_version="=${MPI_VERSION_PIN:?MPI_VERSION_PIN is required}"

  if ((EUID != 0)); then
    apt_command=(sudo -n apt-get)
    install_command=(sudo -n env DEBIAN_FRONTEND=noninteractive apt-get)
    mark_command=(sudo -n apt-mark)
  fi
  "${apt_command[@]}" update -y || return 1
  "${install_command[@]}" install -y \
    --no-upgrade \
    --no-install-recommends \
    libopenmpi-dev \
    "python${DEPLOY_PYTHON_VERSION}-dev" \
    "libopenmpi3t64${mpi_version}" \
    "openmpi-bin${mpi_version}" \
    "openmpi-common${mpi_version}" || return 1
  "${mark_command[@]}" hold libopenmpi3t64 openmpi-bin openmpi-common
}

# trt_install_system_dependencies: Install MPI when the compiler is absent.
# Globals:
#   MPI_VERSION_PIN
# Arguments:
#   None.
# Outputs:
#   Writes installation progress and failures to standard error.
# Returns:
#   0 when mpicc is available, non-zero otherwise.
trt_install_system_dependencies() {
  command -v mpicc >/dev/null 2>&1 && return 0
  command -v apt-get >/dev/null 2>&1 || {
    log_write "[deps] TensorRT host installation requires apt-get"
    return 1
  }
  log_write "[deps] Installing MPI development packages"
  _trt_install_mpi || return 1
  command -v mpicc >/dev/null 2>&1
}
