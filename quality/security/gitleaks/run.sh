#!/usr/bin/env bash
#
# Run Gitleaks with repository-owned baseline state.
set -euo pipefail

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly SCRIPT_DIR
REPO_ROOT="$(CDPATH='' cd -- "${SCRIPT_DIR}/../../.." && pwd -P)"
readonly REPO_ROOT
# shellcheck source=../../config/security/gitleaks/environment.sh
source "${REPO_ROOT}/quality/config/security/gitleaks/environment.sh"

BASELINE_FILE="${REPO_ROOT}/${GITLEAKS_BASELINE_FILE}"
readonly BASELINE_FILE
uv run python -m quality.repository.integrity.gitleaks

gitleaks_args=(detect "${GITLEAKS_FLAGS[@]}" --source "${REPO_ROOT}" --baseline-path "${BASELINE_FILE}")
if [[ -n ${GITLEAKS_LOG_OPTS} ]]; then
  gitleaks_args+=(--log-opts "${GITLEAKS_LOG_OPTS}")
fi

gitleaks "${gitleaks_args[@]}"
