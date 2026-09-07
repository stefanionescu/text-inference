#!/usr/bin/env bash
#
# Run pip-audit against the locked Python environment.
set -euo pipefail

REPO_ROOT="${MISE_PROJECT_ROOT:-$(git rev-parse --show-toplevel)}"
cd "${REPO_ROOT}"

uv run pip-audit \
  --strict \
  --progress-spinner off
