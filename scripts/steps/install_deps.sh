#!/usr/bin/env bash
#
# Install locked host dependencies for the selected inference engine.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

STEP_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly STEP_FOLDER
ROOT_FOLDER="$(CDPATH='' cd -- "${STEP_FOLDER}/../.." && pwd -P)" || exit 1
readonly ROOT_FOLDER
export ROOT_FOLDER

# shellcheck source=scripts/lib/deps/certs.sh
source "${STEP_FOLDER}/../lib/deps/certs.sh"
# shellcheck source=scripts/lib/deps/trt/install.sh
source "${STEP_FOLDER}/../lib/deps/trt/install.sh"
# shellcheck source=scripts/lib/deps/trt/system.sh
source "${STEP_FOLDER}/../lib/deps/trt/system.sh"
# shellcheck source=scripts/lib/deps/uv/environment.sh
source "${STEP_FOLDER}/../lib/deps/uv/environment.sh"
# shellcheck source=scripts/lib/deps/vllm.sh
source "${STEP_FOLDER}/../lib/deps/vllm.sh"
# shellcheck source=scripts/engines/trt/detection.sh
source "${STEP_FOLDER}/../engines/trt/detection.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${STEP_FOLDER}/../lib/foundation/log.sh"

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
  [[ -x ${VENV_FOLDER:?VENV_FOLDER is required}/bin/python ]] || return 1
  [[ -n ${TORCH_CUDA_ARCH_LIST-} ]] || return 1
  certs_install
  certs_export_environment
  uv_export_environment
  _install_engine_dependencies
}

main "$@"
