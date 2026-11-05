#!/usr/bin/env bash
#
# Install and export the host certificate authority bundle.
# Runtime: Bash 3.2+, Linux.
# Boundary: Owns operating-system certificate package installation.

_CERTS_DEPS_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=scripts/config/defaults.sh
source "${_CERTS_DEPS_DIR}/../../config/defaults.sh"
# shellcheck source=scripts/lib/shared/log.sh
source "${_CERTS_DEPS_DIR}/../shared/log.sh"

# _certs_bundle: Print the installed distribution CA bundle path.
_certs_bundle() {
  local bundle
  local -a bundles=(
    "/etc/ssl/certs/ca-certificates.crt"
    "/etc/pki/tls/certs/ca-bundle.crt"
    "/etc/ssl/ca-bundle.pem"
  )

  for bundle in "${bundles[@]}"; do
    if [[ -f ${bundle} ]]; then
      printf '%s\n' "${bundle}"
      return 0
    fi
  done
  return 1
}

# certs_install: Install the system CA bundle when it is absent.
# Globals:
#   EUID
# Arguments:
#   None.
# Outputs:
#   Writes installation failures to standard error.
# Returns:
#   0 when a CA bundle exists, non-zero when installation fails.
certs_install() {
  local -a privilege=()

  _certs_bundle >/dev/null 2>&1 && return 0
  if ((EUID != 0)); then
    privilege=(sudo -n)
  fi
  if command -v apt-get >/dev/null 2>&1; then
    "${privilege[@]}" apt-get update -y || return 1
    "${privilege[@]}" apt-get install -y ca-certificates || return 1
    "${privilege[@]}" update-ca-certificates || return 1
  elif command -v apk >/dev/null 2>&1; then
    "${privilege[@]}" apk add --no-cache ca-certificates || return 1
    "${privilege[@]}" update-ca-certificates || return 1
  elif command -v dnf >/dev/null 2>&1; then
    "${privilege[@]}" dnf install -y ca-certificates || return 1
    "${privilege[@]}" update-ca-trust || return 1
  elif command -v yum >/dev/null 2>&1; then
    "${privilege[@]}" yum install -y ca-certificates || return 1
    "${privilege[@]}" update-ca-trust || return 1
  else
    log_write "[certs] No supported package manager found"
    return 1
  fi
  _certs_bundle >/dev/null
}

# certs_export_environment: Export the installed CA bundle path.
# Globals:
#   CURL_CA_BUNDLE
#   GIT_SSL_CAINFO
#   REQUESTS_CA_BUNDLE
# Arguments:
#   None.
# Outputs:
#   None.
# Returns:
#   0 after exporting an available bundle.
certs_export_environment() {
  local bundle

  bundle="$(_certs_bundle)" || return 1
  cfg_export_default REQUESTS_CA_BUNDLE "${bundle}"
  cfg_export_default CURL_CA_BUNDLE "${bundle}"
  cfg_export_default GIT_SSL_CAINFO "${bundle}"
}
