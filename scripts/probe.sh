#!/usr/bin/env bash
#
# Probe the fixed loopback readiness endpoint.
# Runtime: Bash 3.2+, macOS and Linux.

set -euo pipefail

# main - Return success only while the inference service is ready.
main() {
  (($# == 0)) || return 2
  command -v curl >/dev/null 2>&1 || return 127
  curl \
    --silent \
    --show-error \
    --fail \
    --max-time 2 \
    --connect-timeout 2 \
    http://127.0.0.1:8001/readyz >/dev/null
}

main "$@"
