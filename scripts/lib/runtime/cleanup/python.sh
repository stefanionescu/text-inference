#!/usr/bin/env bash
#
# Discover and remove generated Python cache directories below the repository.
# Runtime: Bash 3.2+, macOS and Linux.
# Boundary: Owns generated Python cache discovery and removal.

_RUNTIME_CLEANUP_PYTHON_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/lib/runtime/cleanup/paths.sh
source "${_RUNTIME_CLEANUP_PYTHON_FOLDER}/paths.sh"

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
  local root_folder="$1"
  local cache_folder
  local manifest
  local removal_status=0

  manifest="$(mktemp "${root_folder}/.cleanup-paths.XXXXXX")" || return 1
  trap 'rm -f -- "${manifest}"; trap - RETURN' RETURN
  find "${root_folder}" \
    -type d \
    \( -name "__pycache__" -o -name ".pytest_cache" \) \
    -print0 >"${manifest}" || return 1
  while IFS= LC_ALL=C read -r -d '' cache_folder; do
    if ! runtime_remove_owned_path "${root_folder}" "${cache_folder}"; then
      removal_status=1
      break
    fi
  done <"${manifest}"
  return "${removal_status}"
}
