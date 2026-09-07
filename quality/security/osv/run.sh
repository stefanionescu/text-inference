#!/usr/bin/env bash
#
# Run OSV Scanner against repository dependency state.
set -euo pipefail

REPO_ROOT="${MISE_PROJECT_ROOT:-$(git rev-parse --show-toplevel)}"
cd "${REPO_ROOT}"

# shellcheck source=../../config/security/osv/environment.sh
source "${REPO_ROOT}/quality/config/security/osv/environment.sh"

osv-scanner scan source \
  --recursive \
  --lockfile "${OSV_LOCKFILE}" \
  --config quality/config/security/osv/config.toml \
  "${REPO_ROOT}"
