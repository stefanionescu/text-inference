#!/usr/bin/env bash
# Shared build argument initialization for Docker builds.
#
# Initializes the BUILD_ARGS array with shared Docker build flags. The parent
# build script must define DOCKERFILE and FULL_IMAGE_NAME before sourcing this
# file. Repo Docker builds are always linux/amd64.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts
# init_build_args: Initialize build args.
init_build_args() {
  local dockerfile="${DOCKERFILE:?DOCKERFILE is required before init_build_args}"
  local full_image_name="${FULL_IMAGE_NAME:?FULL_IMAGE_NAME is required before init_build_args}"

  BUILD_ARGS=(
    --file "${dockerfile}"
    --tag "${full_image_name}"
    --platform "linux/amd64"
  )
  case "${NO_CACHE:?NO_CACHE is required}" in
    0) ;;
    1) BUILD_ARGS+=(--no-cache) ;;
    *)
      log_write "[build] ✗ NO_CACHE must be 0 or 1"
      exit 1
      ;;
  esac
}

# append_model_build_args: Add immutable model inputs to a build.
append_model_build_args() {
  BUILD_ARGS+=(--build-arg "MODEL=${MODEL:?MODEL is required}")
  BUILD_ARGS+=(--build-arg "MODEL_REVISION=${MODEL_REVISION:?MODEL_REVISION is required}")
  [[ -n ${HF_TOKEN-} ]] && BUILD_ARGS+=(--secret "id=hf_token,env=HF_TOKEN")
}
