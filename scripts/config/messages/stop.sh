#!/usr/bin/env bash
#
# Define stop command status messages.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

STOP_USAGE_LINES=(
  "Usage:"
  "  bash scripts/stop.sh"
  "      Stop only repository-recorded process groups."
  ""
  "  bash scripts/stop.sh --reset"
  "      Reset the dedicated inference host, GPU, caches, models, and environments."
)

STOP_MESSAGE_SERVER="[stop] Stopping repository-owned deployment processes"
STOP_MESSAGE_SERVER_DONE="[stop] Repository-owned deployment processes stopped"
STOP_MESSAGE_RESET="[reset] Starting explicit dedicated-host reset"
STOP_MESSAGE_RESET_DONE="[reset] Dedicated-host reset completed"
