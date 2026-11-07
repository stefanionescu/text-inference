#!/usr/bin/env bash
#
# Install locked host dependencies for the selected inference engine.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

# shellcheck source=scripts/lib/foundation/folders.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../lib/foundation/folders.sh"
# shellcheck source=scripts/lib/deps/certs.sh
source "${SCRIPTS_FOLDER}/lib/deps/certs.sh"
# shellcheck source=scripts/lib/deps/trt/install.sh
source "${SCRIPTS_FOLDER}/lib/deps/trt/install.sh"
# shellcheck source=scripts/lib/deps/trt/system.sh
source "${SCRIPTS_FOLDER}/lib/deps/trt/system.sh"
# shellcheck source=scripts/lib/deps/uv/environment.sh
source "${SCRIPTS_FOLDER}/lib/deps/uv/environment.sh"
# shellcheck source=scripts/lib/deps/vllm.sh
source "${SCRIPTS_FOLDER}/lib/deps/vllm.sh"
# shellcheck source=scripts/engines/trt/detection.sh
source "${SCRIPTS_FOLDER}/engines/trt/detection.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${SCRIPTS_FOLDER}/lib/foundation/log.sh"

# _install_engine_dependencies - Install the selected engine dependency set.
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

# main - Install certificates and locked Python dependencies.
main() {
  [[ -x ${VENV_FOLDER:?VENV_FOLDER is required}/bin/python ]] || return 1
  [[ -n ${TORCH_CUDA_ARCH_LIST-} ]] || return 1
  certs_install
  certs_export_environment
  uv_export_environment
  _install_engine_dependencies
}

main "$@"
