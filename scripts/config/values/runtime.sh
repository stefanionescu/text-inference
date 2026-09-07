#!/usr/bin/env bash
#
# Define runtime state and log paths.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # lint:justify -- reason: sourced configuration exports variables consumed by parent scripts -- ticket: N/A
[[ -n ${_CFG_RUNTIME_READY:-} ]] && return 0
readonly _CFG_RUNTIME_READY=1

readonly CFG_RUNTIME_RUN_DIR=".run"
readonly CFG_RUNTIME_LOG_DIR="logs"

readonly CFG_RUNTIME_SERVER_PID_FILE="server.pid"
readonly CFG_RUNTIME_SERVER_LOG_FILE="server.log"
readonly CFG_RUNTIME_SERVER_LOG_TRIM_FILE=".server.log.trim"
readonly CFG_RUNTIME_DEPLOYMENT_PID_FILE=".run/deployment.pid"
readonly CFG_RUNTIME_STATE_FILE=".run/runtime-state.tsv"
readonly CFG_RUNTIME_WARMUP_LOCK_FILE=".run/warmup.lock"
readonly CFG_RUNTIME_WARMUP_LOG_FILE="logs/warmup.log"
readonly CFG_RUNTIME_WARMUP_CAPTURE_FILE="logs/warmup.server.log"
