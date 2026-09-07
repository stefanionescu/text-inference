#!/usr/bin/env bash
#
# Resolve warmup profile variants from configuration or repository defaults.
# Runtime: Bash 3.2+, macOS and Linux.

_WARMUP_PROFILE_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/config/values/deployment.sh
source "${_WARMUP_PROFILE_DIR}/../../../config/values/deployment.sh"

# _warmup_trim - Print a value without surrounding whitespace.
_warmup_trim() {
  local value="$1"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s\n' "${value}"
}

# _warmup_add_profile - Append one normalized profile variant.
_warmup_add_profile() {
  local gender
  local personality

  gender="$(_warmup_trim "$1")" || return 1
  personality="$(_warmup_trim "${2-}")" || return 1
  [[ -n ${gender} ]] || return 0
  WARMUP_PROMPT_PAIRS+=("${gender}|${personality}")
}

# _warmup_parse_profiles - Parse comma-delimited profile configuration.
_warmup_parse_profiles() {
  local specification="$1"
  local entry
  local -a entries

  IFS=',' read -r -a entries <<<"${specification}"
  for entry in "${entries[@]}"; do
    entry="$(_warmup_trim "${entry}")" || return 1
    [[ -n ${entry} ]] || continue
    if [[ ${entry} == *:* ]]; then
      _warmup_add_profile "${entry%%:*}" "${entry#*:}" || return 1
    else
      _warmup_add_profile "${entry}" "" || return 1
    fi
  done
}

# warmup_detect_profiles - Populate profile variants from overrides or Python.
# Globals:
#   GENDER
#   PERSONALITY
#   WARMUP_PROMPT_SELECTION
#   WARMUP_PROMPT_PAIRS
# Arguments:
#   $1: Managed Python executable.
# Outputs:
#   None.
# Returns:
#   0 after populating at least the repository defaults.
warmup_detect_profiles() {
  local python_bin="$1"
  local output=""
  local line

  local prompt_selection="${WARMUP_PROMPT_SELECTION-}"

  WARMUP_PROMPT_PAIRS=()
  if [[ -n ${prompt_selection} ]]; then
    _warmup_parse_profiles "${prompt_selection}" || return 1
  elif [[ -n ${GENDER-} ]]; then
    _warmup_add_profile "${GENDER}" "${PERSONALITY-}" || return 1
  elif output="$("${python_bin}" -m src.scripts.warmup list 2>/dev/null)"; then
    while IFS= read -r line; do
      line="$(_warmup_trim "${line}")" || return 1
      [[ -n ${line} ]] || continue
      _warmup_parse_profiles "${line}" || return 1
    done <<<"${output}"
  fi
  if [[ ${#WARMUP_PROMPT_PAIRS[@]} == 0 ]]; then
    _warmup_add_profile "${CFG_WARMUP_DEFAULT_GENDER_PRIMARY}" "" || return 1
    _warmup_add_profile "${CFG_WARMUP_DEFAULT_GENDER_SECONDARY}" ""
  fi
}
