#!/usr/bin/env bash
#
# Query the first NVIDIA GPU for its identity and compute capability.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns nvidia-smi parsing for host deployment.

_GPU_QUERY_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/lib/shared/log.sh
source "${_GPU_QUERY_DIR}/../log.sh"

# gpu_architecture - Print the supported GPU compute architecture.
# Globals:
#   GPU_SM_ARCH
# Arguments:
#   None.
# Outputs:
#   Writes an sm-prefixed architecture to standard output.
# Returns:
#   0 for a supported architecture, non-zero otherwise.
gpu_architecture() {
  local compute_capability

  if [[ -n ${GPU_SM_ARCH-} ]]; then
    case "${GPU_SM_ARCH}" in
      sm80 | sm86 | sm89 | sm90 | sm100 | sm103 | sm120)
        printf '%s\n' "${GPU_SM_ARCH}"
        return 0
        ;;
      *)
        log_write "[gpu] Unsupported GPU_SM_ARCH: ${GPU_SM_ARCH}"
        return 1
        ;;
    esac
  fi
  compute_capability="$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader)" || return 1
  compute_capability="${compute_capability%%$'\n'*}"
  compute_capability="${compute_capability//./}"
  case "${compute_capability}" in
    80 | 86 | 89 | 90 | 100 | 103 | 120)
      printf 'sm%s\n' "${compute_capability}"
      ;;
    *)
      log_write "[gpu] Unsupported GPU compute capability: ${compute_capability}"
      return 1
      ;;
  esac
}

# gpu_name - Print the first GPU name reported by nvidia-smi.
# Globals:
#   None.
# Arguments:
#   None.
# Outputs:
#   Writes the GPU name to standard output.
# Returns:
#   0 for a non-empty name, non-zero otherwise.
gpu_name() {
  local detected_name

  detected_name="$(nvidia-smi --query-gpu=name --format=csv,noheader)" || return 1
  detected_name="${detected_name%%$'\n'*}"
  [[ -n ${detected_name} ]] || return 1
  printf '%s\n' "${detected_name}"
}
