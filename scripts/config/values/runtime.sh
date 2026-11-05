#!/usr/bin/env bash
#
# Define runtime state and log paths.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

RUNTIME_RUN_FOLDER=".run"
RUNTIME_LOG_FOLDER="logs"

RUNTIME_SERVER_PID_FILE="server.pid"
RUNTIME_SERVER_LOG_FILE="server.log"
RUNTIME_SERVER_TRIM_FILE=".server.log.trim"
RUNTIME_DEPLOYMENT_PID_FILE=".run/deployment.pid"
RUNTIME_STATE_FILE=".run/runtime-state.tsv"
RUNTIME_WARMUP_LOCK_FILE=".run/warmup.lock"
RUNTIME_WARMUP_LOG_FILE="logs/warmup.log"
RUNTIME_WARMUP_CAPTURE_FILE="logs/warmup.server.log"
