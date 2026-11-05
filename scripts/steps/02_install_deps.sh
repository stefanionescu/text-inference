#!/usr/bin/env bash
#
# Install locked host dependencies for the selected inference engine.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

STEP_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly STEP_DIR
ROOT_DIR="$(CDPATH='' cd -- "${STEP_DIR}/../.." && pwd -P)" || exit 1
readonly ROOT_DIR
export ROOT_DIR

# shellcheck source=scripts/lib/deps/certs.sh
source "${STEP_DIR}/../lib/deps/certs.sh"
# shellcheck source=scripts/lib/deps/trt/install.sh
source "${STEP_DIR}/../lib/deps/trt/install.sh"
# shellcheck source=scripts/lib/deps/trt/system.sh
source "${STEP_DIR}/../lib/deps/trt/system.sh"
# shellcheck source=scripts/lib/deps/uv/environment.sh
source "${STEP_DIR}/../lib/deps/uv/environment.sh"
# shellcheck source=scripts/lib/deps/vllm.sh
source "${STEP_DIR}/../lib/deps/vllm.sh"
# shellcheck source=scripts/engines/trt/detection.sh
source "${STEP_DIR}/../engines/trt/detection.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${STEP_DIR}/../lib/shared/log.sh"

# _install_engine_dependencies: Install the selected engine dependency set.
_install_engine_dependencies() {
  case "${INFERENCE_ENGINE:?INFERENCE_ENGINE is required}" in
    trt)
      trt_validate_cuda "deps"
      trt_install_system_dependencies
      trt_install_dependencies
      ;;
    vllm)
      vllm_install_dependencies
      ;;
    *)
      return 2
      ;;
  esac
}

# main: Install certificates and locked Python dependencies.
main() {
  [[ -x ${VENV_DIR:?VENV_DIR is required}/bin/python ]] || return 1
  [[ -n ${TORCH_CUDA_ARCH_LIST-} ]] || return 1
  certs_install
  certs_export_environment
  uv_export_environment
  _install_engine_dependencies
}

main "$@"
