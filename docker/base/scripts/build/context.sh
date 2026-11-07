#!/usr/bin/env bash

# prepare_shared_build_context - Create one engine image build context.
prepare_shared_build_context() {
  local stack_folder="$1"
  local folder_prefix="$2"
  local dockerfile="${DOCKERFILE:?DOCKERFILE is required}"
  local root_folder="${ROOT_FOLDER:?ROOT_FOLDER is required}"

  TEMPORARY_BUILD_FOLDER="$(mktemp -d -t "${folder_prefix}-build-XXXXXX")"
  trap 'rm -rf "${TEMPORARY_BUILD_FOLDER}"' EXIT

  cp -a "${dockerfile}" "${TEMPORARY_BUILD_FOLDER}/Dockerfile"
  cp -a "${stack_folder}/.dockerignore" "${TEMPORARY_BUILD_FOLDER}/.dockerignore"
  cp -a "${root_folder}/pyproject.toml" "${TEMPORARY_BUILD_FOLDER}/pyproject.toml"
  cp -a "${root_folder}/uv.lock" "${TEMPORARY_BUILD_FOLDER}/uv.lock"
  cp -a "${root_folder}/src" "${TEMPORARY_BUILD_FOLDER}/src"
  cp -a "${root_folder}/config" "${TEMPORARY_BUILD_FOLDER}/config"

  mkdir -p "${TEMPORARY_BUILD_FOLDER}/scripts"
  cp -a "${stack_folder}/scripts"/* "${TEMPORARY_BUILD_FOLDER}/scripts/"
  cp -a "${root_folder}/scripts/config" "${TEMPORARY_BUILD_FOLDER}/scripts/config"
  cp -a "${root_folder}/scripts/readiness.sh" "${TEMPORARY_BUILD_FOLDER}/scripts/readiness.sh"
  mkdir -p "${TEMPORARY_BUILD_FOLDER}/scripts/lib/foundation/gpu"
  cp -a \
    "${root_folder}/scripts/lib/foundation/gpu/." \
    "${TEMPORARY_BUILD_FOLDER}/scripts/lib/foundation/gpu/"
  cp -a "${root_folder}/scripts/lib/foundation/log.sh" "${TEMPORARY_BUILD_FOLDER}/scripts/lib/foundation/log.sh"
  mkdir -p "${TEMPORARY_BUILD_FOLDER}/scripts/lib/env"
  cp -a "${root_folder}/scripts/lib/env/trt.sh" "${TEMPORARY_BUILD_FOLDER}/scripts/lib/env/trt.sh"

  mkdir -p "${TEMPORARY_BUILD_FOLDER}/base/scripts"
  cp -a "${root_folder}/docker/base/scripts"/* "${TEMPORARY_BUILD_FOLDER}/base/scripts/"

  mkdir -p "${TEMPORARY_BUILD_FOLDER}/docker/base/download"
  cp -a "${root_folder}/docker/base/download/snapshot.py" "${TEMPORARY_BUILD_FOLDER}/docker/base/download/snapshot.py"

  export BUILD_CONTEXT="${TEMPORARY_BUILD_FOLDER}"
}
