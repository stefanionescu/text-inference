#!/usr/bin/env bash
#
# Define stop command status messages.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

CFG_STOP_USAGE_LINES=(
  "Usage:"
  "  bash scripts/stop.sh"
  "      Stop only repository-recorded process groups."
  ""
  "  bash scripts/stop.sh --reset"
  "      Reset the dedicated inference host, GPU, caches, models, and environments."
)

CFG_STOP_MSG_STOP="[stop] Stopping repository-owned deployment processes"
CFG_STOP_MSG_STOP_DONE="[stop] Repository-owned deployment processes stopped"
CFG_STOP_MSG_RESET="[reset] Starting explicit dedicated-host reset"
CFG_STOP_MSG_RESET_DONE="[reset] Dedicated-host reset completed"
