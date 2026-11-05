#!/usr/bin/env bash
#
# Define repository-wide host deployment values.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

_DEPLOYMENT_VALUES_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=scripts/config/defaults.sh
source "${_DEPLOYMENT_VALUES_FOLDER}/../defaults.sh"

DEFAULT_ENGINE="trt"
DEPLOY_PYTHON_VERSION="3.12"
RUNTIME_VENV_RELATIVE_PATH=".venv"
QUANT_VENV_RELATIVE_PATH=".venv-quant"
DOCKER_DEFAULT_IMAGE_NAME="text-inference"
DOCKER_DEFAULT_NO_CACHE="0"
HF_PUSH_PRIVATE_DEFAULT="1"
LOGS_ENABLED_DEFAULT="0"

MAX_SERVER_LOG_BYTES=$((100 * 1024 * 1024))
WARMUP_TIMEOUT_SECONDS_DEFAULT="300"
WARMUP_RETRIES_DEFAULT="1"
WARMUP_HEALTH_POLL_SECONDS="2"
WARMUP_DELAY_SECONDS_DEFAULT="1"
WARMUP_GENDER_PRIMARY_DEFAULT="female"
WARMUP_GENDER_SECONDARY_DEFAULT="male"
