#!/usr/bin/env bash
#
# Define repository-wide host deployment values.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

_CFG_DEPLOYMENT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=scripts/config/defaults.sh
source "${_CFG_DEPLOYMENT_DIR}/../defaults.sh"

CFG_DEFAULT_ENGINE="trt"
CFG_PYTHON_VERSION="3.12"
CFG_RUNTIME_VENV_DIR_REL=".venv"
CFG_QUANT_VENV_DIR_REL=".venv-quant"
CFG_DOCKER_DEFAULT_IMAGE_NAME="text-inference"
CFG_DOCKER_DEFAULT_NO_CACHE="0"
CFG_HF_PUSH_PRIVATE_DEFAULT="1"
CFG_LOGS_ENABLED_DEFAULT="0"

CFG_MAX_SERVER_LOG_BYTES=$((100 * 1024 * 1024))
CFG_WARMUP_TIMEOUT_SECONDS_DEFAULT="300"
CFG_WARMUP_RETRIES_DEFAULT="1"
CFG_WARMUP_HEALTH_POLL_INTERVAL_SECONDS_DEFAULT="2"
CFG_WARMUP_RUN_DELAY_SECONDS_DEFAULT="1"
CFG_WARMUP_DEFAULT_GENDER_PRIMARY="female"
CFG_WARMUP_DEFAULT_GENDER_SECONDARY="male"
