#!/usr/bin/env bash
#
# Confirm that the host NVIDIA driver is available.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

STEP_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly STEP_DIR

# shellcheck source=scripts/lib/shared/log.sh
source "${STEP_DIR}/../lib/shared/log.sh"

# main: Probe the NVIDIA management interface.
main() {
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    log_write "[gpu] nvidia-smi is required"
    return 1
  fi
  if ! nvidia-smi >/dev/null 2>&1; then
    log_write "[gpu] nvidia-smi could not access a GPU"
    return 1
  fi
}

main "$@"
