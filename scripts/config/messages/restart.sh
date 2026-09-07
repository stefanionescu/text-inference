#!/usr/bin/env bash
#
# Define restart command messages and usage text.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034 # lint:justify -- reason: sourced configuration exports user-facing message values -- ticket: N/A
[[ -n ${_CFG_MSG_RESTART_READY:-} ]] && return 0
readonly _CFG_MSG_RESTART_READY=1

readonly -a CFG_RESTART_USAGE_LINES=(
  "Usage:"
  "  scripts/restart.sh [--engine trt|vllm] [--model MODEL [--quantization FORMAT]]"
  "                     [--reinstall] [--reset] [--push] [--logs]"
  ""
  "Behavior:"
  "  - Without --model, reuses the persisted source and checkpoint."
  "  - --model reconfigures the source; quantization remains opt-in."
  "  - Engine changes and missing or incompatible environments rebuild automatically."
  "  - --reset performs the opt-in dedicated-host process, GPU, cache, and environment reset."
  ""
  "Options:"
  "  --engine trt|vllm  Select the inference engine."
  "  --model MODEL       Select a new source repository or local directory."
  "  --quantization FMT  Export an unquantized source in the exact engine format."
  "  --reinstall         Explicitly rebuild the managed environments."
  "  --reset             Perform the broad host reset before deployment."
  "  --push              Upload a validated repository-provenanced local export."
  "  --logs              Stream third-party runtime and quantization output."
  ""
  "Required environment variables:"
  "  API_KEY, HF_TOKEN, MAX_CONCURRENT_CONNECTIONS"
)
