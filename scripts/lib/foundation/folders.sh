#!/usr/bin/env bash
#
# Resolve the scripts folder and export the repository root for host entry points.
# Runtime: Bash 3.2+, macOS and Linux.

SCRIPTS_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
readonly SCRIPTS_FOLDER
ROOT_FOLDER="$(CDPATH='' cd -- "${SCRIPTS_FOLDER}/.." && pwd -P)"
readonly ROOT_FOLDER
export ROOT_FOLDER
