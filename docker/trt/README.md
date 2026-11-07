# TensorRT-LLM Docker Image

The TensorRT-LLM image serves one immutable ModelOpt checkpoint in Hugging Face
layout through the TensorRT-LLM `1.3.0rc20` public PyTorch backend. It does not
use serialized TensorRT engine directories.

The runtime is text-only, uses one GPU, and defaults `TRT_MAX_BATCH_SIZE` to
`64`.

Complete the common requirements in the
[Docker image guide](../README.md) before building.

## Build the image

Run the build from the repository root:

```shell
DOCKER_USERNAME="<DOCKER_USERNAME>" \
DOCKER_TOKEN="<DOCKER_TOKEN>" \
TAG="trt-model-fp8" \
MODEL="<OWNER>/<REPOSITORY>" \
MODEL_REVISION="<40_CHARACTER_COMMIT_SHA>" \
bash docker/trt/build.sh
```

The build validates the model against the TensorRT allowlist. It also requires
a 40-character Hugging Face commit SHA.

On success, the script pushes
`<DOCKER_USERNAME>/<IMAGE_NAME>:<TAG>` to Docker Hub.

## Select a checkpoint format

The accepted formats are:

- `int4_awq`
- `fp8`
- `nvfp4`

An unquantized source is also valid. The image build does not run NVIDIA Model
Optimizer or convert a checkpoint. It bakes `MODEL` unchanged, detects any
existing format from checkpoint metadata, and rejects only formats that the
TensorRT-LLM backend cannot serve.

Use the format supported by the deployment GPU:

| Format     | Supported GPU architectures             |
| ---------- | --------------------------------------- |
| `int4_awq` | Ampere, Ada, Hopper, and Blackwell      |
| `fp8`      | Ada `sm89` and Hopper `sm90`            |
| `nvfp4`    | Blackwell `sm100`, `sm103`, and `sm120` |

The serving and export stacks use different Model Optimizer versions:

| Component                   | Version        |
| --------------------------- | -------------- |
| TensorRT-LLM                | `1.3.0rc20`    |
| PyTorch                     | `2.10.0+cu130` |
| Transformers                | `5.5.4`        |
| Serving Model Optimizer     | `0.37.0`       |
| Host export Model Optimizer | `0.45.0`       |

## Run the image

```shell
docker run --gpus all --detach \
  --env API_KEY="<API_KEY>" \
  --env MAX_CONCURRENT_CONNECTIONS=8 \
  --publish 8000:8000 \
  <IMAGE>
```

Runtime scheduling and memory remain configurable:

- `TRT_MAX_BATCH_SIZE` limits scheduling capacity.
- `TRT_DTYPE` selects the model dtype.
- `GPU_MEMORY_FRACTION` sets the free-memory fraction available to the KV cache.
- `KV_DTYPE` selects KV-cache storage.
- The entrypoint's `--logs` option streams TensorRT and other dependency output;
  otherwise only repository-owned logs are shown.

These settings do not change the quantized checkpoint.

Replace `<IMAGE>` with the image name printed by the build script.
Append `--logs` after `<IMAGE>` to stream raw dependency output.
