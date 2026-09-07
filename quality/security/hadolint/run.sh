#!/usr/bin/env bash
#
# Run Hadolint when Dockerfiles exist.
set -euo pipefail

REPO_ROOT="${MISE_PROJECT_ROOT:-$(git rev-parse --show-toplevel)}"
cd "${REPO_ROOT}"

# shellcheck source=../../config/security/hadolint/environment.sh
source "${REPO_ROOT}/quality/config/security/hadolint/environment.sh"

dockerfiles=()
# shellcheck disable=SC2312
# lint:justify -- reason: a failed repository search should not mask any Dockerfile lint result.
while IFS= read -r -d '' dockerfile; do
  dockerfiles+=("${dockerfile}")
done < <(
  find . \
    -path './.venv' -prune -o \
    -path './node_modules' -prune -o \
    \( -name 'Dockerfile' -o -name '*.dockerfile' \) \
    -type f \
    -print0
)

if [[ ${#dockerfiles[@]} -eq 0 && ${HADOLINT_SKIP_WITHOUT_DOCKERFILE:-0} == "1" ]]; then
  printf '%s\n' 'skip (no Dockerfiles)'
  exit 0
fi

hadolint "${dockerfiles[@]}"
