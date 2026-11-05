#!/usr/bin/env bash
#
# Define deployment command messages and usage text.
# Runtime: Bash 3.2+, macOS and Linux.

# shellcheck disable=SC2034,SC2016 # reason: sourced configuration exports variables consumed by parent scripts; message config intentionally stores literal shell snippets for user output

CFG_MAIN_USAGE_LINES=(
  "Usage:"
  '  $0 [--engine trt|vllm] --model MODEL [--quantization FORMAT] [--push] [--logs]'
  ""
  "Behavior:"
  "  - Always runs deployment in background (auto-detached)"
  "  - Auto-tails logs (Ctrl+C stops tail, deployment continues)"
  "  - Use scripts/stop.sh to stop the deployment"
  ""
  "Inference Engines:"
  "  --engine X  -> Select trt or vllm (default: trt)"
  ""
  "Quantization:"
  "  vLLM formats: awq, gptq, compressed-tensors, fp8, nvfp4"
  "  TRT formats:  int4_awq, nvfp4, fp8"
  "  --quantization is opt-in; omit it to deploy the source unchanged."
  ""
  "Required environment variables:"
  "  API_KEY='secret'                  - API authentication key"
  "  HF_TOKEN='hf_xxx'                 - Hugging Face access token"
  "  MAX_CONCURRENT_CONNECTIONS=<int>  - Capacity guard limit"
  ""
  "Optional environment:"
  "  GPU_SM_ARCH=sm80|sm89|sm90|sm100|sm103|sm120 - GPU architecture (auto-detected)"
  ""
  "Examples:"
  "  # Deploy a source unchanged with TensorRT-LLM"
  '  $0 --model Qwen/Qwen3-30B-A3B-Instruct-2507'
  ""
  "  # TensorRT-LLM FP8"
  '  $0 --model SicariusSicariiStuff/Impish_Nemo_12B --quantization fp8'
  ""
  "  # vLLM deployment (alternative engine)"
  '  $0 --engine vllm --model SicariusSicariiStuff/Impish_Nemo_12B'
  ""
  "Quantized model uploads:"
  "  --push              Upload a repository-provenanced local export"
  ""
  "Debugging:"
  "  --logs              Stream third-party runtime and quantization logs"
)

CFG_MAIN_MSG_INVALID_ARGS="[main] Not enough arguments"
