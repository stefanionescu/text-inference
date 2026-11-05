#!/usr/bin/env bash
#
# Define quantization defaults for host deployment.
# Runtime: Bash 3.2+, Linux.

# shellcheck disable=SC2034 # reason: sourced configuration exports variables consumed by parent scripts

CFG_QUANT_DEFAULT_MODEL_REVISION="main"
CFG_QUANT_DEFAULT_FORCE_REBUILD="0"
