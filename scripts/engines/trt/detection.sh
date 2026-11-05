#!/usr/bin/env bash
#
# Detect TensorRT checkpoint and CUDA runtime capabilities.
# Runtime: Bash 3.2+, Linux.

_TRT_DETECTION_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/values/trt.sh
source "${_TRT_DETECTION_FOLDER}/../../config/values/trt.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_TRT_DETECTION_FOLDER}/../../lib/foundation/log.sh"

# _trt_version_number: Convert a CUDA major.minor version for comparison.
_trt_version_number() {
  local version="$1"

  if [[ ! ${version} =~ ^([0-9]+)\.([0-9]+)$ ]]; then
    log_write "[cuda] Invalid CUDA version: ${version}"
    return 1
  fi
  printf '%d%02d\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
}

# trt_cuda_version: Print the installed CUDA toolkit version.
# Globals:
#   None.
# Arguments:
#   None.
# Outputs:
#   Writes the CUDA major.minor version to standard output.
# Returns:
#   0 when nvcc reports a version, non-zero otherwise.
trt_cuda_version() {
  local output

  output="$(nvcc --version)" || return 1
  if [[ ! ${output} =~ release[[:space:]]+([0-9]+\.[0-9]+) ]]; then
    log_write "[cuda] Could not read the CUDA toolkit version"
    return 1
  fi
  printf '%s\n' "${BASH_REMATCH[1]}"
}

# trt_validate_cuda: Validate CUDA toolkit and driver minimum versions.
# Globals:
#   TRT_MIN_CUDA_VERSION
# Arguments:
#   $1: Diagnostic phase name.
# Outputs:
#   Writes validation failures to standard error.
# Returns:
#   0 when toolkit and driver satisfy the minimum, non-zero otherwise.
trt_validate_cuda() {
  local phase="$1"
  local minimum
  local toolkit
  local toolkit_number
  local driver
  local driver_number
  local output

  minimum="$(_trt_version_number "${TRT_MIN_CUDA_VERSION}")" || return 1
  toolkit="$(trt_cuda_version)" || return 1
  toolkit_number="$(_trt_version_number "${toolkit}")" || return 1
  if ((toolkit_number < minimum)); then
    log_write "[${phase}] CUDA ${TRT_MIN_CUDA_VERSION}+ required; found ${toolkit}"
    return 1
  fi
  output="$(nvidia-smi)" || return 1
  if [[ ! ${output} =~ CUDA[[:space:]]Version:[[:space:]]([0-9]+\.[0-9]+) ]]; then
    log_write "[${phase}] Could not read NVIDIA driver CUDA capability"
    return 1
  fi
  driver="${BASH_REMATCH[1]}"
  driver_number="$(_trt_version_number "${driver}")" || return 1
  if ((driver_number < minimum)); then
    log_write "[${phase}] NVIDIA driver supports CUDA ${driver}; ${TRT_MIN_CUDA_VERSION}+ required"
    return 1
  fi
}
