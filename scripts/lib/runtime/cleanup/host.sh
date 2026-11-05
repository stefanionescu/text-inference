#!/usr/bin/env bash
#
# Remove inference, compiler, package, and temporary host caches.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns explicit reset cleanup outside repository ownership.

_RUNTIME_RESET_HOST_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/lib/shared/log.sh
source "${_RUNTIME_RESET_HOST_DIR}/../../shared/log.sh"

# _runtime_reset_remove_path: Remove one validated non-root host path.
# Globals:
#   HOME.
# Arguments:
#   $1: Host path selected by the reset policy.
# Outputs:
#   Writes rejected targets to standard error.
# Returns:
#   0 when absent or removed, non-zero when unsafe or removal fails.
_runtime_reset_remove_path() {
  local target_path="$1"
  local parent_path

  [[ -n ${target_path} ]] || return 0
  parent_path="${target_path%/*}"
  case "${target_path}" in
    /*) ;;
    *)
      log_write "[reset] Refusing non-absolute cleanup target: ${target_path}"
      return 2
      ;;
  esac
  case "${target_path}" in
    / | //* | /root | /workspace | /tmp | /dev | /dev/shm | "${HOME:?HOME is required}" | *"/../"* | */..)
      log_write "[reset] Refusing unsafe cleanup target: ${target_path}"
      return 2
      ;;
    *) ;;
  esac
  if [[ -z ${parent_path} || ${parent_path} == "/" ]]; then
    log_write "[reset] Refusing top-level cleanup target: ${target_path}"
    return 2
  fi
  if [[ -e ${target_path} || -L ${target_path} ]]; then
    rm -rf -- "${target_path}"
  fi
}

# _runtime_reset_cache_root: Remove known caches below one cache root.
_runtime_reset_cache_root() {
  local cache_root="$1"
  local name
  local status=0
  local -a names=(
    cuda flashinfer huggingface modelopt nvidia onnx pip pycuda
    tensorrt tensorrt_llm torch torch_extensions triton vllm xformers
  )

  for name in "${names[@]}"; do
    _runtime_reset_remove_path "${cache_root}/${name}" || status=1
  done
  return "${status}"
}

# _runtime_reset_configured_caches: Remove configured and user data caches.
_runtime_reset_configured_caches() {
  local target_path
  local status=0
  local -a paths=(
    "${HF_HOME-}" "${HUGGINGFACE_HUB_CACHE-}" "${TRANSFORMERS_CACHE-}"
    "${PIP_CACHE_DIR-}" "${HOME}/.huggingface" "${HOME}/.config/huggingface"
    "${HOME}/.local/share/huggingface" "${HOME}/.local/share/tensorrt_llm"
    "${HOME}/.nv" "${HOME}/.torch_inductor" "${HOME}/.triton"
    "/root/.huggingface" "/root/.config/huggingface"
    "/root/.local/share/huggingface" "/root/.local/share/tensorrt_llm"
    "/root/.nv" "/root/.torch_inductor" "/root/.triton"
  )

  for target_path in "${paths[@]}"; do
    _runtime_reset_remove_path "${target_path}" || status=1
  done
  return "${status}"
}

# _runtime_reset_temporary_paths: Remove known inference files from temporary roots.
# Globals:
#   None.
# Arguments:
#   None.
# Outputs:
#   None.
# Returns:
#   0 when temporary artifacts are removed, non-zero otherwise.
_runtime_reset_temporary_paths() {
  local status=0

  find /tmp -mindepth 1 -maxdepth 1 \
    \( -name 'vllm*' -o -name 'flashinfer*' -o -name 'torch_*' \
    -o -name 'pip-*' -o -name 'uvicorn*' -o -name 'trtllm*' \
    -o -name 'trt*' -o -name 'tensorrt*' -o -name 'nv*' \
    -o -name 'hf*' -o -name 'cuda*' -o -name 'modelopt*' \
    -o -name 'quantiz*' \) -exec rm -rf -- {} + || status=1
  if [[ -d /dev/shm ]]; then
    find /dev/shm -mindepth 1 -maxdepth 1 \
      \( -name 'tensorrt*' -o -name 'trt*' -o -name 'torch*' \
      -o -name 'nv*' -o -name 'cuda*' -o -name 'hf*' \) \
      -exec rm -rf -- {} + || status=1
  fi
  return "${status}"
}

# runtime_reset_host_caches: Clear all reset-owned host cache locations.
# Globals:
#   HOME, XDG_CACHE_HOME.
# Arguments:
#   None.
# Outputs:
#   Writes unsafe path failures to standard error.
# Returns:
#   0 when every selected cache is removed, non-zero otherwise.
runtime_reset_host_caches() {
  local cache_root
  local status=0
  local -a cache_roots=("${HOME}/.cache" "/root/.cache" "/workspace/.cache")

  if [[ -n ${XDG_CACHE_HOME-} ]]; then
    cache_roots+=("${XDG_CACHE_HOME}")
  fi
  for cache_root in "${cache_roots[@]}"; do
    _runtime_reset_cache_root "${cache_root}" || status=1
  done
  _runtime_reset_configured_caches || status=1
  _runtime_reset_temporary_paths || status=1
  return "${status}"
}
