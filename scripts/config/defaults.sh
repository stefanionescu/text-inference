#!/usr/bin/env bash
#
# Define configuration assignment functions for sourced scripts.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

# config_set_default: Assign a default when a variable is unset or empty.
# Globals:
#   Variable named by the first argument.
# Arguments:
#   $1: Variable name.
#   $2: Default value.
# Outputs:
#   None.
# Returns:
#   0 after assigning or preserving the variable.
config_set_default() {
  local name="$1"
  local default_value="$2"
  local value="${!name:-}"

  if [[ -n ${value} ]]; then
    return 0
  fi
  printf -v "${name}" '%s' "${default_value}"
}

# config_assign_value: Assign a configured value or its declared default.
# Globals:
#   Variable named by the second argument.
# Arguments:
#   $1: Output variable name.
#   $2: Configured variable name.
#   $3: Default value.
# Outputs:
#   None.
# Returns:
#   0 after assigning the output variable.
config_assign_value() {
  local output_name="$1"
  local name="$2"
  local default_value="$3"
  local value="${!name:-}"

  if [[ -n ${value} ]]; then
    printf -v "${output_name}" '%s' "${value}"
    return 0
  fi
  printf -v "${output_name}" '%s' "${default_value}"
}

# config_export_default: Export a default when a variable is unset or empty.
# Globals:
#   Variable named by the first argument.
# Arguments:
#   $1: Variable name.
#   $2: Default value.
# Outputs:
#   None.
# Returns:
#   0 after exporting the variable.
config_export_default() {
  local name="$1"
  local default_value="$2"

  config_set_default "${name}" "${default_value}"
  export "${name?}"
}
