#!/usr/bin/env bash
# shellcheck shell=bash
# lint:justify -- reason: Bearer policy is sourced by scanner scripts -- ticket: quality-security
# shellcheck disable=SC2034

BEARER_SCAN_PATHS=(config src docker quality scripts)
BEARER_FLAGS=(
  --severity "critical,high,medium"
  --format json
  --quiet
  --exit-code 1
)
readonly BEARER_SCAN_PATHS
readonly -a BEARER_FLAGS
