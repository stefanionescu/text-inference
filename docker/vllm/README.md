# vLLM Docker Image

The vLLM image serves one immutable Hugging Face snapshot through vLLM
`0.25.1`. The runtime uses Python 3.12, PyTorch `2.11.0+cu130`, and the vLLM v1
asynchronous engine.

The image is text-only and currently uses one GPU.

Complete the common requirements in the
[Docker image guide](../README.md) before building.

## Build the image

Run the build from the repository root:

```shell
DOCKER_USERNAME="<DOCKER_USERNAME>" \
DOCKER_TOKEN="<DOCKER_TOKEN>" \
TAG="vllm-model-awq" \
MODEL="<OWNER>/<REPOSITORY>" \
MODEL_REVISION="<40_CHARACTER_COMMIT_SHA>" \
bash docker/vllm/build.sh
```

The build validates the model against the vLLM allowlist. It also requires a
40-character Hugging Face commit SHA.

On success, the script pushes
`<DOCKER_USERNAME>/<IMAGE_NAME>:<TAG>` to Docker Hub.

## Checkpoint formats

The accepted formats are:

- `awq`
- `gptq`
- `compressed-tensors`
- `fp8`
- `nvfp4`

An unquantized source is also valid. The image bakes `MODEL` unchanged and does
not run LLM Compressor, apply online quantization, or convert a checkpoint. Its
metadata is inspected during the build and again at runtime; an existing format
is rejected only when it is incompatible with vLLM.

The runtime selects special quantization backends from checkpoint and model
metadata:

- ModelOpt NVFP4 checkpoints use `modelopt_fp4`.
- Qwen 3.5 MoE GPTQ checkpoints use `moe_wna16`.

FlashInfer `0.6.13` is installed for compatible vLLM workloads. The image does
not force FlashInfer for every model. vLLM selects a supported attention
implementation for the loaded model and GPU.

## Run the image

```shell
docker run --gpus all --detach \
  --env API_KEY="<API_KEY>" \
  --env MAX_CONCURRENT_CONNECTIONS=8 \
  --publish 8000:8000 \
  <IMAGE>
```

Set `GPU_MEMORY_FRACTION`, `KV_DTYPE`, or `ENFORCE_EAGER` at runtime when the deployment
needs different memory or execution behavior.

Replace `<IMAGE>` with the image name printed by the build script.
Append `--logs` after `<IMAGE>` to stream raw dependency output.
