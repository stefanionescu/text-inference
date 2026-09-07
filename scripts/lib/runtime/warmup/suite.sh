#!/usr/bin/env bash
#
# Execute warmup and benchmark integration clients for each profile.
# Runtime: Bash 3.2+, macOS and Linux.

_WARMUP_SUITE_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1

# shellcheck source=scripts/lib/runtime/warmup/logging.sh
source "${_WARMUP_SUITE_DIR}/logging.sh"

# _warmup_run_retries - Run one Python integration client with bounded retries.
_warmup_run_retries() {
  local label="$1"
  local prefix="$2"
  local python_bin="$3"
  local retries="$4"
  shift 4
  local attempt
  local run_log=""

  for ((attempt = 1; attempt <= retries; attempt++)); do
    run_log="${LOG_DIR:?LOG_DIR is required}/${prefix}_attempt${attempt}.log"
    printf '[warmup] %s\n' \
      "${label}: attempt ${attempt} -> ${run_log}" \
      >>"${WARMUP_LOG_FILE:?WARMUP_LOG_FILE is required}" || return 1
    if "${python_bin}" "$@" >"${run_log}" 2>&1; then
      warmup_phase_result "${label}" "OK"
      return 0
    fi
  done
  warmup_phase_result "${label}" "FAIL" "${run_log}"
  return 1
}

# _warmup_run_profile - Run warmup and benchmark clients for one profile.
_warmup_run_profile() {
  local profile="$1"
  local maximum_connections="$2"
  local python_bin="$3"
  local retries="$4"
  local gender
  local personality
  local label
  local prefix
  local status=0
  local -a profile_arguments=(env)

  IFS='|' read -r gender personality <<<"${profile}"
  label="${gender}"
  [[ -n ${label} ]] || label="default"
  [[ -z ${gender} ]] || profile_arguments+=(--gender "${gender}")
  [[ -z ${personality} ]] || profile_arguments+=(--personality "${personality}")
  prefix="$(warmup_log_prefix "warmup_${label}")" || return 1
  _warmup_run_retries \
    "warmup: ${label}" "${prefix}" "${python_bin}" "${retries}" \
    -m tests.suites.e2e.test_warmup "${profile_arguments[@]:1}" || status=1
  sleep "${WARMUP_RUN_DELAY_SECONDS:?WARMUP_RUN_DELAY_SECONDS is required}"
  prefix="$(warmup_log_prefix "bench_${maximum_connections}x_${label}")" || return 1
  _warmup_run_retries \
    "warmup: bench ${maximum_connections}x ${label}" "${prefix}" \
    "${python_bin}" "${retries}" -m tests.suites.e2e.test_bench \
    --requests "${maximum_connections}" --concurrency "${maximum_connections}" \
    "${profile_arguments[@]:1}" || status=1
  sleep "${WARMUP_RUN_DELAY_SECONDS}"
  return "${status}"
}

# warmup_run_suite - Run all profile warmup and benchmark probes.
# Globals:
#   WARMUP_PROMPT_PAIRS
#   WARMUP_RETRIES
# Arguments:
#   $1: Maximum benchmark connection count.
#   $2: Managed Python executable.
#   Remaining arguments: Profile variants.
# Outputs:
#   Writes per-probe status and detailed log files.
# Returns:
#   0 when every probe succeeds, non-zero otherwise.
warmup_run_suite() {
  local maximum_connections="$1"
  local python_bin="$2"
  local profile
  local status=0
  local -a profiles

  shift 2
  profiles=("$@")

  for profile in "${profiles[@]}"; do
    _warmup_run_profile \
      "${profile}" "${maximum_connections}" "${python_bin}" \
      "${WARMUP_RETRIES:?WARMUP_RETRIES is required}" || status=1
  done
  return "${status}"
}
