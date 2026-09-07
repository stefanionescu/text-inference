#!/usr/bin/env bash
#
# Wait for the container's fixed loopback readiness probe.

set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=docker/shared/scripts/logs.sh
source "${SCRIPT_DIR}/logs.sh"
# shellcheck source=scripts/config/defaults.sh
source "/app/scripts/config/defaults.sh"

maximum_wait_seconds="${WARMUP_MAX_WAIT_SECONDS-}"
cfg_set_default maximum_wait_seconds "300"
wait_interval_seconds="${WARMUP_WAIT_INTERVAL_SECONDS-}"
cfg_set_default wait_interval_seconds "5"

wait_for_readiness() {
  local elapsed_seconds=0

  log_write "[warmup] Waiting for server readiness"
  while ((elapsed_seconds < maximum_wait_seconds)); do
    if /app/scripts/probe.sh; then
      log_write "[warmup] Server ready after ${elapsed_seconds} seconds"
      return 0
    fi
    sleep "${wait_interval_seconds}"
    elapsed_seconds=$((elapsed_seconds + wait_interval_seconds))
  done
  log_write "[warmup] Server was not ready within ${maximum_wait_seconds} seconds"
  return 1
}

wait_for_readiness
