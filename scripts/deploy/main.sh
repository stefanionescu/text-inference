#!/usr/bin/env bash
#
# Run the detached host deployment pipeline.
# Runtime: Bash 3.2+, Linux.

set -euo pipefail

DEPLOY_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
readonly DEPLOY_DIR
SCRIPTS_DIR="$(CDPATH='' cd -- "${DEPLOY_DIR}/.." && pwd -P)" || exit 1
readonly SCRIPTS_DIR
ROOT_DIR="$(CDPATH='' cd -- "${SCRIPTS_DIR}/.." && pwd -P)" || exit 1
readonly ROOT_DIR
export ROOT_DIR

# shellcheck source=scripts/config/values/deployment.sh
source "${SCRIPTS_DIR}/config/values/deployment.sh"
# shellcheck source=scripts/deploy/environment.sh
source "${DEPLOY_DIR}/environment.sh"
# shellcheck source=scripts/engines/trt/main.sh
source "${SCRIPTS_DIR}/engines/trt/main.sh"
# shellcheck source=scripts/engines/vllm.sh
source "${SCRIPTS_DIR}/engines/vllm.sh"
# shellcheck source=scripts/lib/deps/venv.sh
source "${SCRIPTS_DIR}/lib/deps/venv.sh"
# shellcheck source=scripts/lib/runtime/cleanup/paths.sh
source "${SCRIPTS_DIR}/lib/runtime/cleanup/paths.sh"
# shellcheck source=scripts/lib/shared/deployment.sh
source "${SCRIPTS_DIR}/lib/shared/deployment.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${SCRIPTS_DIR}/lib/shared/log.sh"
# shellcheck source=scripts/lib/shared/publishing.sh
source "${SCRIPTS_DIR}/lib/shared/publishing.sh"
# shellcheck source=scripts/lib/shared/pytorch_guard.sh
source "${SCRIPTS_DIR}/lib/shared/pytorch_guard.sh"

# _deploy_report_exit: Report the captured diagnostics for a failed workflow.
_deploy_report_exit() {
  local status=$?

  trap - EXIT
  if ((status != 0)); then
    log_write "[deploy] Deployment failed; detailed diagnostics: ${ROOT_DIR}/${CFG_RUNTIME_SERVER_LOG_FILE}"
  fi
  exit "${status}"
}

# _deploy_existing_torch_status: Check an existing runtime environment.
_deploy_existing_torch_status() {
  if [[ ! -x ${VENV_DIR:?VENV_DIR is required}/bin/python ]]; then
    return 0
  fi
  pytorch_guard_check "[deploy]"
}

# _deploy_clear_environments: Remove both managed Python environments.
_deploy_clear_environments() {
  runtime_remove_owned_path \
    "${ROOT_DIR}" "${VENV_DIR:?VENV_DIR is required}" || return 1
  runtime_remove_owned_path \
    "${ROOT_DIR}" "${QUANT_VENV_DIR:?QUANT_VENV_DIR is required}"
}

# _deploy_prepare_dependencies: Install dependencies, repairing Torch mismatch.
_deploy_prepare_dependencies() {
  local torch_status=0

  _deploy_existing_torch_status || torch_status=$?
  if ((torch_status == 42)); then
    log_write "[deploy] Torch mismatch requires clean managed environments"
    _deploy_clear_environments || return 1
  elif ((torch_status != 0)); then
    return "${torch_status}"
  fi
  venv_prepare "${VENV_DIR}" || return 1
  bash "${SCRIPTS_DIR}/steps/02_install_deps.sh" || return 1
  torch_status=0
  pytorch_guard_check "[deploy]" || torch_status=$?
  if ((torch_status == 42)); then
    log_write "[deploy] Dependency installation did not repair the Torch mismatch"
  fi
  return "${torch_status}"
}

# _deploy_prepare_checkpoint: Dispatch checkpoint preparation to the selected engine.
_deploy_prepare_checkpoint() {
  case "${INFERENCE_ENGINE:?INFERENCE_ENGINE is required}" in
    trt) trt_prepare_checkpoint ;;
    vllm) vllm_prepare_checkpoint ;;
    *)
      log_write "[deploy] Unsupported inference engine: ${INFERENCE_ENGINE}"
      return 2
      ;;
  esac
}

# main: Execute dependency, checkpoint, and server startup stages.
main() {
  export VENV_DIR="${ROOT_DIR}/${CFG_RUNTIME_VENV_DIR_REL}"
  export QUANT_VENV_DIR="${ROOT_DIR}/${CFG_QUANT_VENV_DIR_REL}"
  bash "${SCRIPTS_DIR}/steps/01_check_gpu.sh"
  deploy_initialize_environment "${ROOT_DIR}"
  deployment_validate_cuda "deploy"
  _deploy_prepare_dependencies
  deployment_validate_model
  publishing_validate
  _deploy_prepare_checkpoint
  bash "${SCRIPTS_DIR}/steps/03_start_server.sh"
  log_write "[deploy] Deployment completed for ${INFERENCE_ENGINE}"
}

trap _deploy_report_exit EXIT
main "$@"
