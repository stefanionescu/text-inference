#!/usr/bin/env bash
#
# Validate Hugging Face export publishing inputs.
# Runtime: Bash 3.2+, Linux.

_PUBLISHING_FOUNDATION_FOLDER="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_PUBLISHING_FOUNDATION_FOLDER}/../../config/defaults.sh"
# shellcheck source=scripts/config/values/deployment.sh
source "${_PUBLISHING_FOUNDATION_FOLDER}/../../config/values/deployment.sh"
# shellcheck source=scripts/lib/foundation/log.sh
source "${_PUBLISHING_FOUNDATION_FOLDER}/log.sh"

# publishing_validate: Validate upload credentials and destination policy.
# Globals:
#   HF_PUSH_PRIVATE, HF_PUSH_REPO_ID, PUSH_REQUESTED.
# Arguments:
#   None.
# Outputs:
#   Writes validation failures to standard error.
# Returns:
#   0 for disabled or valid publishing, non-zero otherwise.
publishing_validate() {
  if [[ ${PUSH_REQUESTED:?PUSH_REQUESTED is required} == "0" ]]; then
    return 0
  fi
  if [[ -z ${HF_PUSH_REPO_ID-} ]]; then
    log_write "[env] --push requires HF_PUSH_REPO_ID"
    return 1
  fi
  config_assign_value HF_PUSH_PRIVATE HF_PUSH_PRIVATE "${HF_PUSH_PRIVATE_DEFAULT}"
  case "${HF_PUSH_PRIVATE}" in
    0 | 1) ;;
    *)
      log_write "[env] HF_PUSH_PRIVATE must be 0 or 1"
      return 1
      ;;
  esac
  export HF_PUSH_PRIVATE HF_PUSH_REPO_ID
}
