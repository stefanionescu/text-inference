#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC2034 # lint:justify -- reason: sourced build helpers consume ROOT_DIR -- ticket: N/A
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SHARED_DIR="${SCRIPT_DIR}/../shared"

# usage - Print TensorRT Docker build help.
usage() {
  cat <<'EOF'
Usage: docker/trt/build.sh

Build and push the TensorRT-LLM public PyTorch backend image.

Required environment:
  DOCKER_USERNAME       Docker Hub username
  DOCKER_TOKEN          Docker Hub access token
  TAG                   Image tag; must start with trt-
  MODEL                 Hugging Face or ModelOpt model repository
  MODEL_REVISION        40-character model commit SHA

Optional environment:
  IMAGE_NAME            Docker image name (default: text-inference)
  HF_TOKEN              Hugging Face token for private repositories
  NO_CACHE              Set to 1 to build without Docker cache
EOF
  exit 0
}

# shellcheck disable=SC2034 # lint:justify -- reason: sourced build helpers consume DOCKERFILE -- ticket: N/A
DOCKERFILE="${SCRIPT_DIR}/Dockerfile"
# shellcheck source=docker/shared/scripts/logs.sh
source "${SHARED_DIR}/scripts/logs.sh"
# shellcheck source=docker/shared/scripts/build/driver.sh
source "${SHARED_DIR}/scripts/build/driver.sh"

if [[ ${1-} == "--help" ]] || [[ ${1-} == "-h" ]]; then
  usage
fi
if (($# != 0)); then
  log_write "[build] ✗ TensorRT build does not accept positional arguments"
  exit 1
fi
run_stack_build "${SCRIPT_DIR}" "text-inference-trt" "trt"
