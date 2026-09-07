#!/usr/bin/env bash
# shellcheck shell=bash
# lint:justify -- reason: Semgrep policy is sourced by the scanner entrypoint -- ticket: quality-security
# shellcheck disable=SC2034

SEMGREP_FLAGS=(
  --error
  --no-rewrite-rule-ids
  --metrics=off
  --disable-version-check
  --exclude=quality/config/security/semgrep/vendor
)
SEMGREP_LOCAL_CONFIGS=(
  quality/config/security/semgrep/vendor/python.yml
  quality/config/security/semgrep/vendor/bandit.yml
  quality/config/security/semgrep/vendor/owasp-top-ten.yml
  quality/config/security/semgrep/vendor/secrets.yml
  quality/config/security/semgrep/vendor/bash.yml
  quality/config/security/semgrep/python.yml
  quality/config/security/semgrep/secrets.yml
  quality/config/security/semgrep/markers.yml
)
SEMGREP_SCAN_PATHS=(
  config
  src
  docker
  tests
  scripts
  quality
)
readonly -a SEMGREP_FLAGS
readonly -a SEMGREP_LOCAL_CONFIGS
readonly -a SEMGREP_SCAN_PATHS
