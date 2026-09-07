#!/usr/bin/env bash
#
# Discover and remove generated Python cache directories below the repository.
# Runtime: Bash 3.2+, macOS and Linux.
# Boundary: Owns generated Python cache discovery and removal.

_RUNTIME_CLEANUP_PYTHON_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/lib/runtime/cleanup/paths.sh
source "${_RUNTIME_CLEANUP_PYTHON_DIR}/paths.sh"

# runtime_cleanup_python_artifacts - Remove discovered Python cache directories.
# Globals:
#   None.
# Arguments:
#   $1: Repository root.
# Outputs:
#   None.
# Returns:
#   0 after removing caches, non-zero on discovery or removal failure.
runtime_cleanup_python_artifacts() {
  local root_dir="$1"
  local cache_dir
  local manifest
  local removal_status=0

  manifest="$(mktemp "${root_dir}/.cleanup-paths.XXXXXX")" || return 1
  if ! find "${root_dir}" \
    -type d \
    \( -name "__pycache__" -o -name ".pytest_cache" \) \
    -print0 >"${manifest}"; then
    rm -f -- "${manifest}"
    return 1
  fi
  while IFS= LC_ALL=C read -r -d '' cache_dir; do
    if ! runtime_remove_owned_path "${root_dir}" "${cache_dir}"; then
      removal_status=1
      break
    fi
  done <"${manifest}"
  rm -f -- "${manifest}"
  return "${removal_status}"
}
