#!/usr/bin/env bash
# Shared validate, build, and push transaction for concrete engine stacks.

_BUILD_DRIVER_FOLDER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=docker/base/scripts/build/docker.sh
source "${_BUILD_DRIVER_FOLDER}/docker.sh"
# shellcheck source=docker/base/scripts/build/args.sh
source "${_BUILD_DRIVER_FOLDER}/args.sh"
# shellcheck source=docker/base/scripts/build/context.sh
source "${_BUILD_DRIVER_FOLDER}/context.sh"
# shellcheck source=docker/base/scripts/build/validate.sh
source "${_BUILD_DRIVER_FOLDER}/validate.sh"
# shellcheck source=scripts/config/values/deployment.sh
source "${ROOT_FOLDER:?ROOT_FOLDER is required}/scripts/config/values/deployment.sh"
# shellcheck source=scripts/lib/deps/venv.sh
source "${ROOT_FOLDER}/scripts/lib/deps/venv.sh"

# run_stack_build - Validate, build, and push one concrete engine image.
run_stack_build() {
  local stack_folder="$1"
  local folder_prefix="$2"
  local engine="$3"

  : "${DOCKER_USERNAME:?DOCKER_USERNAME is required}"
  : "${DOCKER_TOKEN:?DOCKER_TOKEN is required}"
  : "${MODEL:?MODEL is required}"
  : "${TAG:?TAG is required}"
  config_set_default IMAGE_NAME "${DOCKER_DEFAULT_IMAGE_NAME}"
  config_set_default NO_CACHE "${DOCKER_DEFAULT_NO_CACHE}"
  export IMAGE_NAME NO_CACHE

  if [[ ! ${TAG} =~ ^${engine}- ]]; then
    log_write "[build] ✗ TAG must start with '${engine}-'"
    return 1
  fi
  FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME:?IMAGE_NAME is required}:${TAG:?TAG is required}"
  export FULL_IMAGE_NAME

  validate_model_revision
  log_write "[build] Validating ${engine} model configuration..."
  validate_models_for_engine "${engine}" "${MODEL}" "${MODEL_REVISION}"
  require_docker
  printf '%s\n' "${DOCKER_TOKEN}" |
    docker login -u "${DOCKER_USERNAME}" --password-stdin
  log_write "[build] Model checkpoint will be baked into the image"
  log_write "[build]   Model: ${MODEL}"
  log_write "[build]   Revision: ${MODEL_REVISION}"

  prepare_shared_build_context "${stack_folder}" "${folder_prefix}"
  init_build_args
  append_model_build_args

  log_write "[build] Building ${FULL_IMAGE_NAME}..."
  docker build "${BUILD_ARGS[@]}" "${BUILD_CONTEXT}"
  log_write "[build] Pushing ${FULL_IMAGE_NAME}..."
  docker push "${FULL_IMAGE_NAME}"
  log_write "[build] ✓ Pushed ${FULL_IMAGE_NAME}"
}
