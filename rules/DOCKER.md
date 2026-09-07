# Working on Docker

These rules apply to Dockerfiles, `.dockerignore` files, Docker build scripts,
Docker helper Python, runtime shell scripts inside image stacks, downloaded model
artifact code, and Docker-related documentation.

Use this file together with [`GENERAL.md`](GENERAL.md), [`BASH.md`](BASH.md),
[`PYTHON.md`](PYTHON.md), and [`NAMING.md`](NAMING.md). Docker changes often
cross language boundaries, so the stricter owning rule applies.

## Contents

- [Image Stack Ownership](#image-stack-ownership)
- [Source Material Decisions](#source-material-decisions)
- [Build Contexts](#build-contexts)
- [Dockerfile Structure](#dockerfile-structure)
- [Base Images and CUDA](#base-images-and-cuda)
- [Dependency Inputs](#dependency-inputs)
- [Package Installation](#package-installation)
- [Python in Images](#python-in-images)
- [Shell in Images](#shell-in-images)
- [Models and Artifacts](#models-and-artifacts)
- [Hugging Face Downloads](#hugging-face-downloads)
- [Secrets](#secrets)
- [Runtime Environment](#runtime-environment)
- [Entrypoints and Health](#entrypoints-and-health)
- [`.dockerignore`](#dockerignore)
- [Layering and Cache Discipline](#layering-and-cache-discipline)
- [Security](#security)
- [Linting](#linting)
- [Documentation](#documentation)
- [Review Checklist](#review-checklist)

## Image Stack Ownership

This repository has two image stacks:

- `docker/vllm/`
- `docker/trt/`

Rules:

- Do not assume a root `Dockerfile`.
- Each stack owns its Dockerfile, build script, runtime scripts, download
  helpers, README, and `.dockerignore`.
- Shared Docker behavior belongs under `docker/common/`.
- Shared behavior must be real. Do not move stack-specific logic into
  `docker/common/` just because two files look similar.
- Keep vLLM-specific behavior in `docker/vllm/`.
- Keep TensorRT-LLM behavior in `docker/trt/`.
- Keep host-side repository scripts under `scripts/`; keep image-build and
  image-runtime scripts under `docker/`.

Bad:

```text
docker/Dockerfile
docker/common/start_everything.sh
```

Good:

```text
docker/vllm/Dockerfile
docker/vllm/scripts/main.sh
docker/trt/Dockerfile
docker/trt/scripts/main.sh
docker/common/scripts/server.sh
```

## Source Material Decisions

These rules adapt Dockerfile best practices, Hadolint guidance, BuildKit secret
handling, NVIDIA CUDA image constraints, and this repository's runtime model.

| Topic                | Local decision                                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| Stack ownership      | `docker/vllm/` and `docker/trt/` are separate image stacks.                                     |
| Shared Docker code   | `docker/common/` owns only behavior that is truly common to both stacks.                        |
| Dependency authority | `pyproject.toml` and `uv.lock` are canonical. Generated requirements are compatibility exports. |
| Runtime Python       | Images must target the repository Python version from `pyproject.toml` and `mise.toml`.         |
| Shell                | Image scripts follow [`BASH.md`](BASH.md).                                                      |
| Docker lint          | Hadolint is the Docker lint authority through `mise run lint:docker`.                           |
| Security             | Docker security checks come from Hadolint plus the repository security task.                    |
| Secrets              | BuildKit secrets and runtime environment variables are allowed. Baked secrets are forbidden.    |
| Model downloads      | Remote model downloads must validate required inputs before network work starts.                |
| CUDA                 | CUDA and GPU libraries are stack-owned runtime dependencies, not host cache copies.             |
| Generated files      | Do not hand-edit dependency exports. Regenerate them from source inputs.                        |

## Build Contexts

Rules:

- Build from the repository root only when the Dockerfile needs repository-wide
  source, generated dependency exports, or shared scripts.
- Keep stack build scripts responsible for choosing the Dockerfile and build
  context.
- Do not hide build inputs in the developer shell. Build scripts must declare
  required environment variables and fail before Docker starts when they are
  missing.
- Do not copy `.venv`, caches, local model directories, logs, or `.artifacts`
  into the build context.
- Do not rely on files ignored by the stack-local `.dockerignore`.
- Keep build arguments explicit. A build argument is part of the image contract.

Build scripts should make the stack obvious:

```bash
docker build \
  --file docker/vllm/Dockerfile \
  --tag "${image_tag}" \
  --build-arg "MODEL=${MODEL}" \
  .
```

Do not build by changing directories and relying on ambient paths:

```bash
cd docker/vllm
docker build .
```

## Dockerfile Structure

Order Dockerfiles like this:

1. Parser directives such as `# syntax=...`.
2. `ARG` values needed by `FROM`.
3. `FROM`.
4. Stack identity labels and non-secret build args.
5. Environment values that describe runtime behavior.
6. System package installation.
7. Python and runtime dependency installation.
8. Source and script copies.
9. Model or artifact download and validation.
10. Runtime user, workdir, exposed ports, healthcheck, and entrypoint.

Rules:

- Put related operations in the same layer when they form one installation
  transaction.
- Split unrelated operations into separate layers when it improves cache reuse
  or review.
- Keep `RUN` blocks readable. Long shell bodies belong in reviewed scripts.
- Do not put fragile application logic directly in a Dockerfile when a Python or
  Bash owner exists.
- Use JSON-array form for `ENTRYPOINT` and `CMD`.
- Keep the final image contract obvious: workdir, exposed ports, environment,
  healthcheck, and entrypoint.

Bad:

```dockerfile
RUN python - <<'PY'
...
PY
```

Good:

```dockerfile
RUN python -m docker.common.download.validate
```

## Base Images and CUDA

Rules:

- Use stack-appropriate CUDA, PyTorch, vLLM, or TensorRT base images.
- Pin base images by explicit tags. Do not use `latest`.
- Do not switch CUDA major versions casually. CUDA version changes affect PyTorch
  wheels, TensorRT-LLM, vLLM, FlashInfer, and GPU driver compatibility.
- Keep CUDA runtime libraries in the image stack that needs them.
- Do not copy host CUDA directories or GPU driver files into images.
- Do not assume the build host has a GPU. Build-time validation must distinguish
  host checks from image runtime checks.
- Runtime GPU checks belong in runtime scripts or health/warmup flows, not in
  build steps unless the build step truly requires a GPU.
- TRT image behavior may install PyTorch or TensorRT-LLM separately when wheel
  compatibility depends on CUDA. Document that behavior in the owning Dockerfile
  or script.

## Dependency Inputs

`pyproject.toml` and `uv.lock` are canonical. The Dockerfiles consume generated
compatibility exports:

- `requirements-vllm.txt`
- `requirements-trt.txt`

These files are generated by:

```bash
mise run deps:export
```

Rules:

- Do not hand-edit generated requirements exports.
- Do not add dependencies only in a Dockerfile when they belong in
  `pyproject.toml`.
- Do not add a runtime package to a development-only dependency group.
- Do not install optional dependencies for the wrong stack.
- Keep vLLM, TRT, local, and llmcompressor dependency surfaces separate.
- After changing dependency source inputs, regenerate dependency exports and
  verify them when the user requested verification.
- Do not introduce a second lockfile or stack-specific dependency authority.

## Package Installation

Rules:

- Combine apt update, package install, and apt cache cleanup in one `RUN` block.
- Use `--no-install-recommends` unless a recommended package is deliberately
  required.
- Pin packages when the repository already pins that package family or when the
  package affects runtime compatibility.
- Remove package manager cache in the same layer that creates it.
- Do not pipe network data directly into a shell.
- Use binary wheels for runtime dependencies when practical.
- Do not use `setup.py install`.
- Do not install tools globally just to make a one-off build step easier.
- Keep system package installation separate from model artifact downloads.

Good:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
```

Bad:

```dockerfile
RUN apt-get update
RUN apt-get install -y curl
```

## Python in Images

Rules:

- Python helper code in `docker/` follows [`PYTHON.md`](PYTHON.md).
- Call helper modules with `python -m`.
- Do not patch `sys.path` in Docker helper Python.
- Do not embed non-trivial inline Python in Dockerfiles or shell scripts.
- Keep download validation, model allowlist checks, and structured parsing in
  Python modules.
- Keep stack-specific download logic in the stack's `download/` package.
- Keep common validation in `docker/common/download/`.
- Do not import product runtime modules from Docker helper code unless the
  import is part of a deliberate boundary and does not trigger runtime setup.

## Shell in Images

Rules:

- Docker shell scripts follow [`BASH.md`](BASH.md).
- Runtime scripts must be directly auditable. Do not hide startup behavior in
  Dockerfile `CMD` strings.
- Sourced Docker shell libraries must not run main behavior when sourced.
- Validate required environment variables before starting model servers.
- Do not enable debug tracing around tokens, model repository names when they
  are sensitive, or request payloads.
- Use arrays for server command arguments.
- Keep `exec` in final server handoff paths so signals reach the server process.
- Avoid background processes unless the script owns cleanup and signal handling.

## Models and Artifacts

Rules:

- Model IDs, engine labels, quantization modes, and artifact paths are image
  contracts.
- Validate model IDs and engine labels before downloading artifacts.
- Keep downloaded artifacts under explicit image paths.
- Do not copy host model caches into images.
- Do not bake local absolute paths into image metadata.
- Do not store prompt payloads, private test conversations, or request bodies in
  image layers.
- Distinguish source models, quantized checkpoints, TRT engines, tokenizer
  files, and generated metadata by name and path.
- Treat engine build metadata as a runtime contract. Do not silently change its
  schema inside Docker scripts.

TRT artifacts and vLLM model artifacts are not interchangeable. A Docker change
that touches one stack must not quietly change the other stack's artifact
contract.

## Hugging Face Downloads

Rules:

- Validate required Hugging Face repository inputs before network calls.
- Validate Docker build revisions where the Docker build contract requires a
  pinned remote artifact.
- Use `HF_TOKEN` only as a secret or runtime environment variable.
- Do not echo token values.
- Do not put token values in build args, labels, image tags, logs, or generated
  files.
- Use explicit cache directories when cache location matters.
- Fail with actionable messages for missing token, missing repo, invalid
  revision, missing files, or download failure.
- Keep Hugging Face API calls inside Python helper modules or clearly owned
  shell boundaries.
- Do not add broad retries. Use bounded retries only for known network
  transient failures.

## Secrets

Rules:

- Never bake Hugging Face tokens, API keys, credentials, or prompt payloads into
  an image layer.
- Use BuildKit secrets for build-time credentials.
- Use runtime environment variables for runtime credentials.
- Keep secret IDs descriptive but not secret-valued.
- Do not write secrets to intermediate files, shell traces, image labels, or
  generated READMEs.
- Do not add secret defaults.
- Do not log full environment dumps in Docker scripts.

Good:

```dockerfile
RUN --mount=type=secret,id=hf_token \
    HF_TOKEN="$(cat /run/secrets/hf_token)" python -m docker.vllm.download.model
```

Bad:

```dockerfile
ARG HF_TOKEN
RUN python -m docker.vllm.download.model --token "${HF_TOKEN}"
```

## Runtime Environment

Rules:

- Environment variables that configure the server are part of the runtime
  contract.
- Keep runtime defaults in the owning config modules and scripts.
- Do not duplicate defaults across Dockerfile, shell, and Python unless the
  value is explicitly part of the image contract.
- Prefer explicit `ENV` declarations for values the image owns.
- Do not export environment variables that only a local shell function needs.
- Keep `MODEL`, `INFERENCE_ENGINE`, `QUANTIZATION`, tokenizer settings, GPU
  settings, and server port behavior consistent with `src/runtime/settings.py`.
- Keep Docker README environment tables in sync with build scripts and
  Dockerfiles.

## Entrypoints and Health

Rules:

- Entrypoints must validate configuration before starting the model server.
- Runtime scripts must surface actionable failure messages.
- Health checks should check the serving process or endpoint, not just whether a
  shell started.
- Warmup should be explicit. Do not hide warmup failures behind successful
  container start.
- Signal handling must allow graceful shutdown of the server process.
- Log enough runtime state to diagnose engine selection, model path, port,
  quantization mode, and GPU configuration without printing secrets.
- Do not start multiple long-lived processes unless the script owns process
  supervision.

## `.dockerignore`

Every image stack must have a stack-local `.dockerignore`.

Rules:

- Exclude local caches, virtual environments, artifacts, logs, and secrets.
- Exclude `.git`, `.venv`, `.artifacts`, test output, and package manager caches
  unless a stack has a documented reason to include them.
- Do not hide source, generated dependency exports, or scripts the Dockerfile
  needs.
- Keep `.dockerignore` changes reviewed with the Dockerfile that depends on
  them.
- Do not use broad ignore patterns that accidentally remove stack-owned scripts
  from the build context.

## Layering and Cache Discipline

Rules:

- Copy dependency metadata before source when doing so improves cache reuse.
- Copy source only after dependency installation when source changes should not
  invalidate dependency layers.
- Do not optimize for cache reuse by making build behavior opaque.
- Keep expensive downloads in layers whose inputs are explicit.
- Do not leave package caches, temporary build directories, or credentials in
  final layers.
- Use multi-stage builds when they meaningfully keep build tools out of runtime
  images.
- Do not add multi-stage complexity for one small copy operation.

## Security

Rules:

- Treat Docker lint and security findings as real until proven otherwise.
- Fix Docker issues directly instead of adding broad ignores.
- Keep suppressions narrow and explain the concrete false positive or platform
  constraint.
- Do not run containers as root unless the image stack requires it and the
  reason is documented.
- Do not grant extra Linux capabilities by default.
- Do not disable TLS verification.
- Do not download executable code without pinning and validation.
- Do not use world-writable directories unless the runtime requires them and the
  path is scoped.
- Do not add SSH keys, cloud credentials, local config files, or package-manager
  auth files to images.
- Keep Hadolint, Gitleaks, OSV, pip-audit, Bandit, Semgrep, Bearer, CodeQL, and
  license policy aligned with repository tasks.

## Linting

Run Docker lint with:

```bash
mise run lint:docker
```

Security scans run through the repository security task:

```bash
mise run security
```

Rules:

- Do not run linting or security scans unless the user asks for verification.
- When verification is requested, prefer the repository task over ad hoc tool
  invocations.
- If a Docker lint failure points at shell behavior, fix the shell script under
  [`BASH.md`](BASH.md).
- If a Docker lint failure points at Python helper behavior, fix the Python
  module under [`PYTHON.md`](PYTHON.md).
- Do not add scanner baselines to avoid real findings.

## Documentation

Rules:

- Docker READMEs document current build and runtime contracts.
- Keep examples copy-pasteable from the repository root unless the README says
  otherwise.
- Do not document secrets with real-looking values.
- Do not mention removed tools or historical behavior.
- Keep Docker docs aligned with build args, environment variables, image tags,
  exposed ports, and artifact paths.
- Keep stack-specific docs in the stack directory.
- Keep shared Docker docs under `docker/` or `docker/common/`.

## Review Checklist

Before accepting a Docker change, check:

- Does the change touch the correct image stack?
- Is shared behavior truly shared?
- Are build inputs explicit and validated before network or Docker work?
- Are dependency changes made in `pyproject.toml` and regenerated exports rather
  than hand-edited requirements?
- Are CUDA, PyTorch, TensorRT-LLM, vLLM, and FlashInfer compatibility constraints
  preserved?
- Are Hugging Face tokens and other secrets kept out of layers, logs, labels,
  and build args?
- Are model IDs, revisions required by Docker builds, engine labels, and
  artifact paths validated?
- Do runtime scripts follow Bash rules and use `exec` for final server handoff?
- Do Python helpers follow Python rules and avoid `sys.path` patching?
- Does each stack-local `.dockerignore` include necessary files and exclude
  local state?
- Are Hadolint and security findings fixed directly instead of broadly ignored?
- Are Docker docs updated for changed build args, env vars, ports, paths, and
  artifact contracts?
