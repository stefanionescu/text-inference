#!/usr/bin/env bash
#
# Define validation patterns and engine identifiers for sourced scripts.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

PATTERN_NON_NEGATIVE_INT='^[0-9]+$'
PATTERN_POSITIVE_INT='^[1-9][0-9]*$'
PATTERN_BINARY_FLAG='^[01]$'
PATTERN_POSITIVE_FRACTION='^(0\.[0-9]*[1-9][0-9]*|1(\.0+)?)$'
PATTERN_QWEN_MOE_SUFFIX='-a[0-9]+b'

ENGINE_TRT="trt"
ENGINE_VLLM="vllm"
