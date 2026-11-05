#!/usr/bin/env bash

# prepare_shared_build_context: Create one engine image build context.
# Globals:
#   DOCKERFILE
#   ROOT_DIR
#   TMP_BUILD_DIR
#   BUILD_CONTEXT
# Arguments:
#   $1: Folder of the engine stack.
#   $2: Prefix of the temporary build folder.
prepare_shared_build_context() {
  local stack_dir="$1"
  local tmp_prefix="$2"
  local dockerfile="${DOCKERFILE:?DOCKERFILE is required}"
  local root_dir="${ROOT_DIR:?ROOT_DIR is required}"

  TMP_BUILD_DIR="$(mktemp -d -t "${tmp_prefix}-build-XXXXXX")"
  trap 'rm -rf "${TMP_BUILD_DIR}"' EXIT

  cp -a "${dockerfile}" "${TMP_BUILD_DIR}/Dockerfile"
  cp -a "${stack_dir}/.dockerignore" "${TMP_BUILD_DIR}/.dockerignore"
  cp -a "${root_dir}/pyproject.toml" "${TMP_BUILD_DIR}/pyproject.toml"
  cp -a "${root_dir}/uv.lock" "${TMP_BUILD_DIR}/uv.lock"
  cp -a "${root_dir}/src" "${TMP_BUILD_DIR}/src"
  cp -a "${root_dir}/config" "${TMP_BUILD_DIR}/config"

  mkdir -p "${TMP_BUILD_DIR}/scripts"
  cp -a "${stack_dir}/scripts"/* "${TMP_BUILD_DIR}/scripts/"
  cp -a "${root_dir}/scripts/config" "${TMP_BUILD_DIR}/scripts/config"
  cp -a "${root_dir}/scripts/probe.sh" "${TMP_BUILD_DIR}/scripts/probe.sh"
  mkdir -p "${TMP_BUILD_DIR}/scripts/lib/shared/gpu"
  cp -a \
    "${root_dir}/scripts/lib/shared/gpu/." \
    "${TMP_BUILD_DIR}/scripts/lib/shared/gpu/"
  cp -a "${root_dir}/scripts/lib/shared/log.sh" "${TMP_BUILD_DIR}/scripts/lib/shared/log.sh"
  mkdir -p "${TMP_BUILD_DIR}/scripts/lib/env"
  cp -a "${root_dir}/scripts/lib/env/trt.sh" "${TMP_BUILD_DIR}/scripts/lib/env/trt.sh"

  mkdir -p "${TMP_BUILD_DIR}/shared/scripts"
  cp -a "${root_dir}/docker/shared/scripts"/* "${TMP_BUILD_DIR}/shared/scripts/"

  mkdir -p "${TMP_BUILD_DIR}/docker/shared/download"
  cp -a "${root_dir}/docker/shared/download/snapshot.py" "${TMP_BUILD_DIR}/docker/shared/download/snapshot.py"

  export BUILD_CONTEXT="${TMP_BUILD_DIR}"
}
