#!/usr/bin/env bash
#
# Define runtime state and log paths.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

CFG_RUNTIME_RUN_DIR=".run"
CFG_RUNTIME_LOG_DIR="logs"

CFG_RUNTIME_SERVER_PID_FILE="server.pid"
CFG_RUNTIME_SERVER_LOG_FILE="server.log"
CFG_RUNTIME_SERVER_LOG_TRIM_FILE=".server.log.trim"
CFG_RUNTIME_DEPLOYMENT_PID_FILE=".run/deployment.pid"
CFG_RUNTIME_STATE_FILE=".run/runtime-state.tsv"
CFG_RUNTIME_WARMUP_LOCK_FILE=".run/warmup.lock"
CFG_RUNTIME_WARMUP_LOG_FILE="logs/warmup.log"
CFG_RUNTIME_WARMUP_CAPTURE_FILE="logs/warmup.server.log"
