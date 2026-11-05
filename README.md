# Text Inference Server

This is an authenticated WebSocket server for streaming text
generation on NVIDIA GPUs. Each deployment serves one model through either
TensorRT-LLM or vLLM.

The public API is text-only, and each engine currently runs on one GPU. A
session can carry a profile prompt and imported conversation history. The
server streams generated text. Clients can cancel active generation or
interrupt it by sending a new turn.

Operational controls cover separate concerns:

- API-key authentication protects the WebSocket endpoint.
- Connection admission and per-connection rate limits protect runtime capacity.
- Health checks, structured logs, and optional telemetry expose runtime state.
- Host scripts and Docker images provide two deployment paths.

## Contents

- [Requirements](#requirements)
- [Start the server](#start-the-server)
- [Choose an engine and format](#choose-an-engine-and-format)
- [Quantized checkpoints](#quantized-checkpoints)
- [Use the WebSocket API](#use-the-websocket-api)
- [Configure the runtime](#configure-the-runtime)
- [Operate a host deployment](#operate-a-host-deployment)
- [Build Docker images](#build-docker-images)
- [Develop the project](#develop-the-project)
- [Inspect health and logs](#inspect-health-and-logs)
- [Troubleshoot startup](#troubleshoot-startup)

## Requirements

Host deployment requires:

- Linux with a supported NVIDIA GPU and driver.
- CUDA 13.x support. The TensorRT-LLM host path requires CUDA 13.1 or later.
- Python 3.12 through the repository-managed environments.
- A Hugging Face token that can read the selected model.
- An allowlisted Hugging Face model or a local model directory.

Install `mise` for the host workflow. Docker builds additionally require Docker
BuildKit and Docker Hub credentials because the build scripts push the finished
image.

GPU memory requirements depend on the model, checkpoint format, sequence
length, and concurrency settings. The deployment scripts do not choose a
smaller model automatically.

## Start the server

Run the setup command from the repository root:

```shell
mise run setup
```

Set the required deployment values:

```shell
export API_KEY="<API_KEY>"
export HF_TOKEN="<HF_TOKEN>"
export MAX_CONCURRENT_CONNECTIONS=8
```

Start TensorRT-LLM with a ready INT4-AWQ checkpoint. Quantization is detected
from the checkpoint metadata, so no export option is needed:

```shell
bash scripts/main.sh \
  --model yapwithai/readyart-broken-tutu-24B-transgression-v2.0-trt-awq
```

TensorRT-LLM is the default engine. Select vLLM explicitly:

```shell
bash scripts/main.sh \
  --engine vllm \
  --model warshanks/Ministral-8B-Instruct-2410-AWQ
```

These examples use prequantized checkpoints, so startup does not run a local
calibration export.

Deployment continues in the background. The command tails `server.log` after
startup. Pressing `Control+C` stops the log tail without stopping the server.

## Choose an engine and format

`--model` is required for a fresh deployment. Omit `--quantization` to deploy
the source unchanged, whether it is unquantized or already quantized. Add
`--quantization FORMAT` only when an unquantized source must be exported into
one of these formats:

| Engine       | Accepted formats                                    |
| ------------ | --------------------------------------------------- |
| TensorRT-LLM | `int4_awq`, `fp8`, `nvfp4`                          |
| vLLM         | `awq`, `gptq`, `compressed-tensors`, `fp8`, `nvfp4` |

TensorRT-LLM applies this GPU policy:

| Format     | Supported GPU architectures             |
| ---------- | --------------------------------------- |
| `int4_awq` | Ampere, Ada, Hopper, and Blackwell      |
| `fp8`      | Ada `sm89` and Hopper `sm90`            |
| `nvfp4`    | Blackwell `sm100`, `sm103`, and `sm120` |

Format support also depends on the model architecture and the selected
quantizer. The model must appear in the allowlist for the chosen engine unless
the host deployment uses a local directory. Requesting quantization for an
already-quantized source fails instead of converting it. An existing format
that the selected engine cannot serve also fails before caches or environments
are changed.

## Quantized checkpoints

A checkpoint is the model directory loaded by an inference engine. It contains
the model config, safetensors weights, tokenizer assets, and quantization
metadata. It is not a running server or a serialized TensorRT engine.

The repository detects quantization from that metadata. A prequantized
checkpoint is served unchanged when its format is compatible with the selected
engine.

Host deployment can prepare an unquantized source in these cases:

- vLLM can export a `compressed-tensors` W4A16 checkpoint with LLM Compressor.
- vLLM can apply online FP8 quantization when `fp8` is selected.
- TensorRT-LLM can export `int4_awq`, `fp8`, or `nvfp4` checkpoints with
  NVIDIA Model Optimizer.

Every local export preserves tokenizer assets and writes
`quantization_metadata.json`.

The cache identity covers:

- The immutable Hub source revision or local source fingerprint.
- The inference engine and checkpoint format.
- The quantizer version and pinned revision when applicable.
- The selected recipe.
- Every calibration input that affects the export.

The metadata records the exported checkpoint quantization config separately.
It also records execution provenance:

- The quantization GPU and SM architecture.
- The CUDA and Python versions.
- The creation time.

These provenance fields do not make a portable checkpoint specific to the
machine that produced it.

Cache reuse depends on the source and every output-affecting quantization
setting. Set `QUANT_FORCE_REBUILD=1` to rebuild a matching checkpoint.

TensorRT-LLM consumes portable ModelOpt Hugging Face checkpoints. The project
does not build or publish serialized `rank*.engine` files. Serving-time batch
size, sequence limits, and KV-cache memory remain runtime settings.

INT8 W8A8 and SmoothQuant remain available to vLLM through compatible
`compressed-tensors` checkpoints. TensorRT-LLM does not expose `int8_sq`
because ModelOpt does not export that format in the unified Hugging Face schema
required by the public PyTorch backend.

## Use the WebSocket API

Connect to `ws://<HOST>:8000/ws` with either authentication header:

```text
X-API-Key: <API_KEY>
Authorization: Bearer <API_KEY>
```

Every client frame puts `type` and protocol version `v` at the top level.
Only fields such as `history` and `sampling` use the documented nested
structures.

Start one session:

```json
{
    "type": "start",
    "v": 1,
    "gender": "female",
    "personality": "flirty",
    "prompt": "You are concise and conversational.",
    "history": [
        {
            "role": "user",
            "content": "Previous user message"
        },
        {
            "role": "assistant",
            "content": "Previous assistant reply"
        }
    ],
    "sampling": {
        "temperature": 0.8,
        "top_p": 0.95
    }
}
```

After the server confirms the session with a `done` frame, send a generation
turn:

```json
{
    "type": "message",
    "v": 1,
    "user_utterance": "Answer in one sentence."
}
```

Normal generation emits `token` frames followed by `final` and `done`.
Clients can send `cancel`, `ping`, or `end` as separate control frames.

## Configure the runtime

Host deployment requires these values:

| Variable                     | Purpose                                                  |
| ---------------------------- | -------------------------------------------------------- |
| `API_KEY`                    | Authenticates WebSocket clients.                         |
| `HF_TOKEN`                   | Downloads source and checkpoint files from Hugging Face. |
| `MAX_CONCURRENT_CONNECTIONS` | Limits admitted WebSocket connections.                   |

The host command sets the model from `--model`. Runtime quantization is detected
from the resolved checkpoint; the optional `--quantization` value is an export
request, not persistent server configuration.

Common host runtime settings are:

| Variable              | Default    | Purpose                                                 |
| --------------------- | ---------- | ------------------------------------------------------- |
| `MODEL_REVISION`      | `main`     | Selects a host source branch, tag, or commit.           |
| `GPU_MEMORY_FRACTION` | `0.90`     | Limits the GPU-memory fraction available to the engine. |
| `KV_DTYPE`            | GPU policy | Selects `auto` or `fp8` KV-cache storage.               |
| `TRT_DTYPE`           | `auto`     | Selects the TensorRT model dtype.                       |
| `TRT_MAX_BATCH_SIZE`  | `64`       | Limits TensorRT scheduling capacity.                    |
| `ENFORCE_EAGER`       | `0`        | Disables vLLM CUDA graphs when set to `1`.              |

`MAX_CONCURRENT_CONNECTIONS` and `TRT_MAX_BATCH_SIZE` control different
boundaries. The first limits admitted WebSocket sessions. The second limits how
many generation sequences TensorRT-LLM can schedule at once.

A batch limit of `64` is a ceiling, not a throughput guarantee. Available
KV-cache memory and request sequence lengths determine how much concurrent
generation work fits on the GPU.

See [.env.example](.env.example) for supported host deployment and server
variables.

## Operate a host deployment

Restart the current deployment with its selected model request:

```shell
bash scripts/restart.sh
```

Reconfigure the model and engine. Model and requested-quantization changes
invalidate the relevant caches; engine changes also replace incompatible
environments automatically:

```shell
bash scripts/restart.sh \
  --engine vllm \
  --model <MODEL> \
  --quantization compressed-tensors
```

Use `--reinstall` for an explicit dependency rebuild. A missing environment,
engine change, host reset, or Torch/TorchVision repair triggers the same rebuild
without that flag. Add `--logs` to either deploy or restart command to stream
third-party output that is quiet by default.

Stop the server while preserving environments and model caches:

```shell
bash scripts/stop.sh
```

Reset the dedicated inference host only when you intend to terminate all GPU
compute processes, reset the GPU, and remove managed environments, models,
runtime state, logs, and inference/package caches:

```shell
bash scripts/stop.sh --reset
```

Publish a locally exported checkpoint by adding `--push` and setting:

```shell
export HF_PUSH_REPO_ID="<OWNER>/<REPOSITORY>"
export HF_PUSH_PRIVATE=1
```

The upload uses `HF_TOKEN`, which must have write access to the destination.
Publishing accepts a validated local checkpoint with repository provenance and
rejects remote prequantized checkpoints.

## Build Docker images

Docker images bake one immutable Hugging Face snapshot into one engine-specific
image. The build scripts require a 40-character Hugging Face commit SHA.

Build and push a vLLM image:

```shell
DOCKER_USERNAME="<DOCKER_USERNAME>" \
DOCKER_TOKEN="<DOCKER_TOKEN>" \
TAG="vllm-model-awq" \
MODEL="<OWNER>/<REPOSITORY>" \
MODEL_REVISION="<40_CHARACTER_COMMIT_SHA>" \
bash docker/vllm/build.sh
```

Build and push a TensorRT-LLM image:

```shell
DOCKER_USERNAME="<DOCKER_USERNAME>" \
DOCKER_TOKEN="<DOCKER_TOKEN>" \
TAG="trt-model-fp8" \
MODEL="<OWNER>/<REPOSITORY>" \
MODEL_REVISION="<40_CHARACTER_COMMIT_SHA>" \
bash docker/trt/build.sh
```

Run either image with the required runtime values:

```shell
docker run --gpus all --detach \
  --name text-inference \
  --env API_KEY="<API_KEY>" \
  --env MAX_CONCURRENT_CONNECTIONS=8 \
  --publish 8000:8000 \
  <IMAGE>
```

Replace `<IMAGE>` with the image reference pushed by the build script.
Append `--logs` after `<IMAGE>` to stream raw dependency and runtime output.

See the [Docker image guide](docker/README.md) for build requirements and
engine-specific checkpoint contracts.

## Develop the project

The repository uses Python 3.12, `uv`, and `mise`. Dependency environments
remain separate because the serving engines require incompatible vendor
stacks.

The pinned runtime versions are:

| Component                       | Version     |
| ------------------------------- | ----------- |
| TensorRT-LLM                    | `1.3.0rc20` |
| vLLM                            | `0.25.1`    |
| NVIDIA Model Optimizer exporter | `0.45.0`    |
| LLM Compressor                  | `0.12`      |
| Python                          | `3.12`      |

Install dependencies:

```shell
mise run setup
```

Run the repository checks:

```shell
mise run deps:verify
bunx --no-install gspot check
mise run test
mise run test:unit
mise run test:integration
```

`mise run test:e2e -- [CLIENT_ARGS]` runs the four finite clients. Use the
individual `test:e2e:*` tasks for warmup, benchmark, conversation, history, or
the interactive live client. E2E clients accept `--server`, `--api-key`,
`--timeout`, and `--sanitize`; the transaction timeout defaults to 120 seconds,
and output sanitization is opt-in.

## Inspect health and logs

Check process liveness or serving readiness on the fixed loopback listener:

```shell
curl --fail http://127.0.0.1:8001/healthz
curl --fail http://127.0.0.1:8001/readyz
```

Inspect server output:

```shell
tail --follow server.log
```

Port 8000 exposes only `/ws`. Port 8001 binds only to `127.0.0.1` and is never
published by the Docker images. `/healthz` reports process liveness;
`/readyz` returns 200 only after runtime initialization and public WebSocket
acceptance, and returns 503 while starting or draining.

## Troubleshoot startup

Start with `server.log` and loopback `/readyz`. The most common failures have direct
causes:

- A configuration error names the missing or invalid environment variable.
- A model validation error means the remote repository is not allowlisted for
  the selected engine. Local model directories bypass the Hub allowlist.
- A quantization mismatch means the checkpoint metadata does not declare the
  requested format.
- A calibration out-of-memory error requires smaller calibration settings or
  a model that fits the available GPU.
- A client connection failure usually means the API key, protocol order, or
  connection limit is wrong.
