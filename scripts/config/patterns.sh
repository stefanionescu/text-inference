#!/usr/bin/env bash
#
# Define validation patterns and engine identifiers for sourced scripts.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # lint:justify -- reason: sourced configuration exports variables consumed by parent scripts -- ticket: N/A
[[ -n ${_CFG_PATTERNS_READY:-} ]] && return 0
readonly _CFG_PATTERNS_READY=1

readonly CFG_PATTERN_NON_NEGATIVE_INT='^[0-9]+$'
readonly CFG_PATTERN_POSITIVE_INT='^[1-9][0-9]*$'
readonly CFG_PATTERN_BINARY_FLAG='^[01]$'
readonly CFG_PATTERN_POSITIVE_FRACTION='^(0\.[0-9]*[1-9][0-9]*|1(\.0+)?)$'
readonly CFG_PATTERN_QWEN_MOE_SUFFIX='-a[0-9]+b'

readonly CFG_ENGINE_TRT="trt"
readonly CFG_ENGINE_VLLM="vllm"
