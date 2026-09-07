# Docker Images

The repository builds separate images for vLLM and TensorRT-LLM. Each image
contains one engine and one immutable Hugging Face model snapshot. There is no
runtime backend router.

The build scripts perform one transaction:

1. Validate the build inputs.
1. Build the engine-specific image from the locked dependency set.
1. Push the finished image to Docker Hub.

## Requirements

Before building an image:

- Start Docker with BuildKit support.
- Set `DOCKER_TOKEN` to a Docker Hub access token.
- Set `DOCKER_USERNAME` to the destination Docker Hub namespace.
- Select an allowlisted Hugging Face repository.
- Resolve `MODEL_REVISION` to a 40-character Hugging Face commit SHA.
- Set `HF_TOKEN` when the model repository is private or gated.

The build rejects branches, tags, and abbreviated commit hashes. This keeps the
model snapshot inside the image reproducible.

## Common build inputs

| Variable          | Required | Default          | Purpose                                                   |
| ----------------- | :------: | ---------------- | --------------------------------------------------------- |
| `DOCKER_USERNAME` |   Yes    | None             | Selects the Docker Hub namespace.                         |
| `DOCKER_TOKEN`    |   Yes    | None             | Authenticates the image push without storing a password.  |
| `TAG`             |   Yes    | None             | Selects the engine-prefixed image tag.                    |
| `MODEL`           |   Yes    | None             | Selects an allowlisted Hugging Face repository.           |
| `MODEL_REVISION`  |   Yes    | None             | Selects an immutable 40-character commit SHA.             |
| `IMAGE_NAME`      |    No    | `text-inference` | Selects the image repository name.                        |
| `HF_TOKEN`        |    No    | None             | Reads a private or gated model through a BuildKit secret. |
| `NO_CACHE`        |    No    | `0`              | Disables Docker layer reuse when set to `1`.              |

`TAG` must start with `vllm-` for vLLM or `trt-` for TensorRT-LLM. The pushed
image is `<DOCKER_USERNAME>/<IMAGE_NAME>:<TAG>`.

## Build a vLLM image

```shell
DOCKER_USERNAME="<DOCKER_USERNAME>" \
DOCKER_TOKEN="<DOCKER_TOKEN>" \
TAG="vllm-model-awq" \
MODEL="<OWNER>/<REPOSITORY>" \
MODEL_REVISION="<40_CHARACTER_COMMIT_SHA>" \
bash docker/vllm/build.sh
```

The image bakes the selected checkpoint unchanged. Validation detects its
existing format and rejects it only when vLLM cannot serve that format. Docker
builds never quantize models.

See the [vLLM image contract](vllm/README.md) before selecting the checkpoint.

## Build a TensorRT-LLM image

```shell
DOCKER_USERNAME="<DOCKER_USERNAME>" \
DOCKER_TOKEN="<DOCKER_TOKEN>" \
TAG="trt-model-fp8" \
MODEL="<OWNER>/<REPOSITORY>" \
MODEL_REVISION="<40_CHARACTER_COMMIT_SHA>" \
bash docker/trt/build.sh
```

The image bakes the selected checkpoint unchanged. Validation detects its
existing format and rejects it only when TensorRT-LLM cannot serve that format.

See the [TensorRT-LLM image contract](trt/README.md) for checkpoint metadata
and GPU compatibility.

## Run an image

Both images require an API key and a positive connection limit at runtime:

```shell
docker run --gpus all --detach \
  --name text-inference \
  --env API_KEY="<API_KEY>" \
  --env MAX_CONCURRENT_CONNECTIONS=8 \
  --publish 8000:8000 \
  <IMAGE>
```

The model and detected checkpoint format are fixed at build time. Runtime configuration
remains available through the same environment variables documented in the
[host runtime guide](../README.md#configure-the-runtime).

Replace `<IMAGE>` with the image name printed by the build script.

Check the container after startup:

```shell
docker exec text-inference \
  curl --fail http://127.0.0.1:8001/readyz
```

Only port 8000 is published, and it serves `/ws` only. The liveness and
readiness listener stays inside the container on loopback port 8001. Append
`--logs` after `<IMAGE>` to stream otherwise-suppressed dependency output.

## Troubleshoot a build or container

- If revision validation fails, use the full 40-character Hugging Face commit
  SHA rather than a branch, tag, or abbreviated hash.
- If model validation fails, select a repository from the allowlist for the
  chosen engine.
- If the build succeeds but the push fails, authenticate to Docker Hub and
  verify that `DOCKER_USERNAME` owns the destination namespace.
- If the container exits during startup, check `API_KEY`,
  `MAX_CONCURRENT_CONNECTIONS`, and the checkpoint format.
- If the container is not ready, inspect `server.log` inside it and run the
  fixed loopback readiness check shown above.
