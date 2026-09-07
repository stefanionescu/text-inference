#!/usr/bin/env bash
#
# Define quantization defaults for host deployment.
# Runtime: Bash 3.2+, Linux.

# shellcheck disable=SC2034 # lint:justify -- reason: sourced configuration exports variables consumed by parent scripts -- ticket: N/A
[[ -n ${_CFG_QUANTIZATION_READY:-} ]] && return 0
readonly _CFG_QUANTIZATION_READY=1

readonly CFG_QUANT_DEFAULT_MODEL_REVISION="main"
readonly CFG_QUANT_DEFAULT_FORCE_REBUILD="0"
