#!/usr/bin/env bash
#
# Define repository-wide host deployment values.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # lint:justify -- reason: sourced configuration exports variables consumed by parent scripts -- ticket: N/A
[[ -n ${_CFG_DEPLOYMENT_READY:-} ]] && return 0
readonly _CFG_DEPLOYMENT_READY=1

_CFG_DEPLOYMENT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1
readonly _CFG_DEPLOYMENT_DIR
# shellcheck source=scripts/config/defaults.sh
source "${_CFG_DEPLOYMENT_DIR}/../defaults.sh"

readonly CFG_DEFAULT_ENGINE="trt"
readonly CFG_PYTHON_VERSION="3.12"
readonly CFG_RUNTIME_VENV_DIR_REL=".venv"
readonly CFG_QUANT_VENV_DIR_REL=".venv-quant"
readonly CFG_DOCKER_DEFAULT_IMAGE_NAME="text-inference"
readonly CFG_DOCKER_DEFAULT_NO_CACHE="0"
readonly CFG_HF_PUSH_PRIVATE_DEFAULT="1"
readonly CFG_LOGS_ENABLED_DEFAULT="0"

readonly CFG_MAX_SERVER_LOG_BYTES=$((100 * 1024 * 1024))
readonly CFG_WARMUP_TIMEOUT_SECONDS_DEFAULT="300"
readonly CFG_WARMUP_RETRIES_DEFAULT="1"
readonly CFG_WARMUP_HEALTH_POLL_INTERVAL_SECONDS_DEFAULT="2"
readonly CFG_WARMUP_RUN_DELAY_SECONDS_DEFAULT="1"
readonly CFG_WARMUP_DEFAULT_GENDER_PRIMARY="female"
readonly CFG_WARMUP_DEFAULT_GENDER_SECONDARY="male"
