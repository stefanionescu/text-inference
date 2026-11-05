#!/usr/bin/env bash
set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SHARED_DIR="${SCRIPT_DIR}/../shared"

# usage: Print vLLM Docker build help.
usage() {
  cat <<'EOF'
Usage: docker/vllm/build.sh

Build and push the Text Inference vLLM image.

Required environment:
  DOCKER_USERNAME       Docker Hub username
  DOCKER_TOKEN          Docker Hub access token
  TAG                   Image tag; must start with vllm-
  MODEL                 Hugging Face model repository
  MODEL_REVISION        40-character model commit SHA

Optional environment:
  IMAGE_NAME            Docker image name (default: text-inference)
  HF_TOKEN              Hugging Face token for private repos
  NO_CACHE              Set to 1 to build without Docker cache
EOF
  exit 0
}

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts
DOCKERFILE="${SCRIPT_DIR}/Dockerfile"

# Modules - shared Docker utilities
# shellcheck source=docker/shared/scripts/logs.sh
source "${SHARED_DIR}/scripts/logs.sh"
# shellcheck source=docker/shared/scripts/build/driver.sh
source "${SHARED_DIR}/scripts/build/driver.sh"

# No command-line flags supported except --help
# main: Reject unexpected arguments, then build the vLLM image.
main() {
  if [[ ${1-} == "--help" ]] || [[ ${1-} == "-h" ]]; then
    usage
  fi
  if (($# != 0)); then
    log_write "[build] ✗ vLLM build does not accept positional arguments"
    exit 1
  fi
  run_stack_build "${SCRIPT_DIR}" "text-inference-vllm" "vllm"
}

main "$@"
