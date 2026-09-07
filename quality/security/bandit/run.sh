#!/usr/bin/env bash
#
# Run Bandit security checks.
set -euo pipefail

REPO_ROOT="${MISE_PROJECT_ROOT:-$(git rev-parse --show-toplevel)}"
cd "${REPO_ROOT}"

uv run bandit -c pyproject.toml -r config src docker quality
