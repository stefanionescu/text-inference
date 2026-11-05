# Text inference reference guide

This guide is for operators and maintainers who already understand the normal
deployment path in the [README](README.md). It defines the exact runtime and
protocol contracts. It also explains engine tuning, observability, and
diagnostic work.

Each server process has five fixed boundaries:

- `--model` selects one deployed large language model (LLM).
- `--engine` selects one inference backend.
- One tokenizer renders prompts and measures every token budget.
- The authenticated `/ws` endpoint owns client sessions.
- Liveness and readiness stay on a fixed loopback-only listener.

## Contents

- [Runtime architecture](#runtime-architecture)
- [Configuration reference](#configuration-reference)
- [Host operations](#host-operations)
- [WebSocket API: `/ws`](#websocket-api-ws)
- [Prompt, history, and sampling](#prompt-history-and-sampling)
- [Inference engines](#inference-engines)
- [Quantization](#quantization)
- [Docker images](#docker-images)
- [Telemetry](#telemetry)
- [Logging](#logging)
- [Health checks](#health-checks)
- [Developer workflow](#developer-workflow)
- [Test clients](#test-clients)
- [Troubleshooting](#troubleshooting)

## Runtime architecture

### Process lifecycle

The process entrypoint is `src.server.trt` for TensorRT-LLM or
`src.server.vllm` for vLLM. Both entrypoints create the same public FastAPI
application, a separate probe application, and inject an engine-specific
factory. One event loop owns both listeners:

- `0.0.0.0:8000` serves `/ws` only.
- `127.0.0.1:8001` serves `/healthz` and `/readyz` only.

Startup follows this sequence:

1. Select one engine-specific application entrypoint.
1. Configure contextual Python logging.
1. Read and validate the process environment.
1. Initialize configured telemetry backends.
1. Create the inference engine and tokenizer.
1. Create connection admission and session runtime state.
1. Start the vLLM cache-reset coordinator when the engine supports it.
1. Start the public and probe listeners.
1. Mark readiness after runtime initialization and public socket acceptance.
1. Accept authenticated WebSocket sessions.

Shutdown aborts active requests before releasing engine resources and flushing
telemetry.

The process uses the `spawn` multiprocessing method before engine startup.
This prevents child processes from inheriting an initialized Compute Unified
Device Architecture (CUDA) context on the graphics processing unit (GPU).

### Runtime dependency ownership

The application creates its runtime dependencies once during startup:

- Connection admission state.
- The session runtime.
- The selected inference engine.
- The model tokenizer.
- The immutable settings snapshot.
- The vLLM cache-reset coordinator when supported.

WebSocket handling receives these dependencies explicitly. Request code does
not fetch a global engine or initialize a service on first use.

## Configuration reference

### Required deployment values

Host deployment requires a named model argument and three environment
variables:

| Value                        | Description                                                        |
| ---------------------------- | ------------------------------------------------------------------ |
| `--model MODEL`              | Selects a Hugging Face repository or local model directory.        |
| `API_KEY`                    | Authenticates clients that connect to `/ws`.                       |
| `HF_TOKEN`                   | Allows host scripts to download or publish Hugging Face artifacts. |
| `MAX_CONCURRENT_CONNECTIONS` | Sets the positive WebSocket admission limit.                       |

The host command defaults to TensorRT-LLM. Use `--engine vllm` to select vLLM.

### Engine and model variables

| Variable              | Default | Description                                       |
| --------------------- | ------- | ------------------------------------------------- |
| `MODEL_REVISION`      | `main`  | Host source branch, tag, or commit.               |
| `QUANT_FORCE_REBUILD` | `0`     | Ignore a matching local quantized checkpoint.     |
| `TRT_DTYPE`           | `auto`  | TensorRT model dtype.                             |
| `TRT_MAX_BATCH_SIZE`  | `64`    | Maximum sequences TensorRT can schedule together. |
| `ENFORCE_EAGER`       | `0`     | Disable vLLM CUDA graphs when set to `1`.         |

For remote sources, the host resolves `MODEL_REVISION` to an immutable commit
before quantization or cache matching.

Startup fails when:

- `--model` is missing.
- `API_KEY` is missing.
- `MAX_CONCURRENT_CONNECTIONS` is missing or less than `1`.
- `--engine` is not `trt` or `vllm`.
- TensorRT dtype, KV dtype, or maximum batch settings are invalid.
- The detected checkpoint format is incompatible with the selected engine.
- You request quantization for an already-quantized source.
- Tokenizer validation cannot find the model tokenizer files.

### GPU variables

| Variable              | Default    | Description                                                                |
| --------------------- | ---------- | -------------------------------------------------------------------------- |
| `GPU_MEMORY_FRACTION` | `0.90`     | Engine-specific GPU memory fraction. Valid range: `0.01` to `1.0`.         |
| `KV_DTYPE`            | GPU policy | KV cache dtype preference.                                                 |
| `GPU_SM_ARCH`         | Detected   | Overrides the detected architecture with a value such as `sm80` or `sm90`. |

vLLM uses `GPU_MEMORY_FRACTION` as its GPU-memory utilization target. TensorRT-LLM passes
the value to its KV-cache free-memory fraction.

Architecture notes:

| SM architecture           | Typical GPU           | TensorRT formats    |
| ------------------------- | --------------------- | ------------------- |
| `sm80`                    | A100                  | `int4_awq`          |
| `sm86`                    | RTX 30 series         | `int4_awq`          |
| `sm89`                    | L40S or RTX 40 series | `int4_awq`, `fp8`   |
| `sm90`                    | H100 or H200          | `int4_awq`, `fp8`   |
| `sm100`, `sm103`, `sm120` | Blackwell             | `int4_awq`, `nvfp4` |

### Prompt and history variables

| Variable                       | Default | Description                                               |
| ------------------------------ | ------- | --------------------------------------------------------- |
| `PROMPT_MAX_TOKENS`            | `1500`  | Maximum client prompt tokens in `start`.                  |
| `HISTORY_MAX_TOKENS`           | `3000`  | Token threshold for imported and session history.         |
| `USER_UTTERANCE_MAX_TOKENS`    | `500`   | Maximum current user utterance tokens.                    |
| `HISTORY_RETENTION_PERCENTAGE` | `66`    | Percent of history budget retained after trimming.        |
| `CONTEXT_BUFFER`               | `25`    | Safety buffer included in `MAXIMUM_CONTEXT_LENGTH`.       |
| `MAXIMUM_OUTPUT_TOKENS`        | `150`   | Maximum generation tokens.                                |
| `STREAM_FLUSH_MILLISECONDS`    | `0`     | Optional token coalescing delay. `0` disables coalescing. |
| `TEMPLATE_ENABLE_THINKING`     | `0`     | Enables tokenizer thinking mode when set to `1`.          |

Derived values:

| Value                    | Formula                                                                               | Default |
| ------------------------ | ------------------------------------------------------------------------------------- | ------- |
| `MAXIMUM_CONTEXT_LENGTH` | `PROMPT_MAX_TOKENS + HISTORY_MAX_TOKENS + USER_UTTERANCE_MAX_TOKENS + CONTEXT_BUFFER` | `5025`  |
| Engine sequence capacity | `MAXIMUM_CONTEXT_LENGTH + MAXIMUM_OUTPUT_TOKENS`                                      | `5175`  |
| `TRIMMED_HISTORY_LENGTH` | `HISTORY_MAX_TOKENS * HISTORY_RETENTION_PERCENTAGE // 100`                            | `1980`  |

`TRIMMED_HISTORY_LENGTH` must stay below `HISTORY_MAX_TOKENS`.

### Sampling variables

| Variable             | Default | Valid range     |
| -------------------- | ------- | --------------- |
| `TEMPERATURE`        | `0.8`   | `0.0` to `1.2`  |
| `TOP_P`              | `0.95`  | `0.6` to `1.0`  |
| `TOP_K`              | `30`    | `0` to `60`     |
| `MIN_P`              | `0.0`   | `0.0` to `0.20` |
| `REPETITION_PENALTY` | `1.0`   | `1.0` to `1.3`  |
| `PRESENCE_PENALTY`   | `0.0`   | `0.0` to `0.5`  |
| `FREQUENCY_PENALTY`  | `0.0`   | `0.0` to `0.5`  |

Per-request overrides use the same lowercase field names. A frame can place the
fields in a nested `sampling` object or at the top level.

### WebSocket variables

| Variable                                      | Default | Description                           |
| --------------------------------------------- | ------- | ------------------------------------- |
| `WEBSOCKET_PROTOCOL_VERSION`                  | `1`     | Required `v` value in client frames.  |
| `WEBSOCKET_MAX_MESSAGE_BYTES`                 | `65536` | Maximum raw message size.             |
| `WEBSOCKET_IDLE_TIMEOUT_SECONDS`              | `150`   | Idle close timeout.                   |
| `WEBSOCKET_WATCHDOG_TICK_SECONDS`             | `10`    | Idle watchdog poll interval.          |
| `WEBSOCKET_HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS` | `0.5`   | Time to wait for a connection slot.   |
| `WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS`         | `60`    | Rolling rate-limit window in seconds. |
| `WEBSOCKET_MESSAGES_PER_WINDOW`               | `20`    | Per-connection message limit.         |
| `WEBSOCKET_CANCELS_PER_WINDOW`                | `20`    | Per-connection cancel limit.          |
| `AUTHENTICATION_FAILURE_LIMIT`                | `10`    | Per-client auth failure throttle.     |

Close codes:

| Code   | Meaning                                                         |
| ------ | --------------------------------------------------------------- |
| `1000` | Normal client-requested close.                                  |
| `1008` | Policy violation, usually authentication or validation failure. |
| `1013` | Server busy.                                                    |
| `4000` | Idle timeout.                                                   |

### Timeout variables

| Variable                     | Default | Description                                    |
| ---------------------------- | ------- | ---------------------------------------------- |
| `GENERATION_TIMEOUT_SECONDS` | `60`    | Generation timeout. Valid range: `1` to `600`. |

### Logging variables

| Variable                | Default | Description                                 |
| ----------------------- | ------- | ------------------------------------------- |
| `APPLICATION_LOG_LEVEL` | `INFO`  | Sets the root and application logger level. |

The server uses one fixed log format. Every record includes:

- Session identifier in `session_id`.
- Request identifier in `request_id`.
- Client identifier in `client_id`.
- Logger name.
- Timestamp.
- Message.

### Docker build-time variables

Docker builds require an immutable Hugging Face commit SHA. Build inputs do not
become WebSocket parameters.

| Image        | Entrypoint             | Required variables                                                  |
| ------------ | ---------------------- | ------------------------------------------------------------------- |
| vLLM         | `docker/vllm/build.sh` | `DOCKER_USERNAME`, `DOCKER_TOKEN`, `TAG`, `MODEL`, `MODEL_REVISION` |
| TensorRT-LLM | `docker/trt/build.sh`  | `DOCKER_USERNAME`, `DOCKER_TOKEN`, `TAG`, `MODEL`, `MODEL_REVISION` |

For a gated repository, set `HF_TOKEN`. The build passes it as a BuildKit secret.

## Host operations

### Full deployment

```shell
bash scripts/main.sh [--engine trt|vllm] --model MODEL [--quantization FORMAT] [--push] [--logs]
```

The main script:

- Validates authentication inputs, resolves the source revision, and inspects
  model metadata before cache deletion or dependency work.
- Deploys unquantized or compatible prequantized sources unchanged when the
  command omits `--quantization`.
- Exports only an unquantized source when the command includes `--quantization`.
- Installs the dependencies for the selected engine.
- Prepares or reuses a repository-provenanced local export when requested.
- Starts the dual-listener server process in a detached session.
- Records the process identifier (PID) in `server.pid`.
- Appends server output to `server.log`.
- Waits for loopback `/readyz` and runs the warmup client.
- Tails the server log in the foreground.

Pressing `Control+C` detaches from the log tail. It does not stop the server.

### Main script examples

The first TensorRT example requests a ModelOpt export from an unquantized
source. The remaining examples serve compatible checkpoints unchanged.

```shell
# TensorRT-LLM INT4-AWQ export from an unquantized source
bash scripts/main.sh \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --quantization int4_awq

# TensorRT-LLM serves an existing compatible checkpoint unchanged
bash scripts/main.sh --model <PREQUANTIZED_MODEL>

# vLLM serves an existing AWQ checkpoint unchanged
bash scripts/main.sh \
  --engine vllm \
  --model warshanks/Ministral-8B-Instruct-2410-AWQ

# TensorRT-LLM with raw dependency logs
bash scripts/main.sh --model <MODEL> --logs
```

Verbose switches:

| Flag     | Description                                                        |
| -------- | ------------------------------------------------------------------ |
| `--logs` | Stream raw runtime, quantization, subprocess, and dependency logs. |

### Restart

```shell
bash scripts/restart.sh
```

Quick restarts preserve the selected source, resolved checkpoint, detected
runtime format, and any requested export format as separate state. Switching
engines automatically removes incompatible environments and rebuilds
dependencies.

Reconfigure the model and optionally request a new export:

```shell
bash scripts/restart.sh \
  --engine vllm \
  --model <UNQUANTIZED_MODEL> \
  --quantization compressed-tensors
```

Useful restart flags:

| Flag          | Description                                                           |
| ------------- | --------------------------------------------------------------------- |
| `--reinstall` | Explicitly rebuild managed dependencies before relaunch.              |
| `--reset`     | Reset dedicated-host GPU, process, cache, and environment state.      |
| `--push`      | Upload a validated repository-produced or reused local export.        |
| `--logs`      | Stream raw dependency, runtime, quantization, and warmup diagnostics. |

### Stop

A light stop ends the server and related processes. It preserves virtual
environments, Hugging Face caches, and model artifacts:

```shell
bash scripts/stop.sh
```

An explicit dedicated-host reset also:

- Terminates broad inference helper matches and every NVIDIA compute PID.
- Resets the GPU.
- Removes virtual environments.
- Removes repository and host inference/compiler/package caches.
- Removes model and runtime artifacts.
- Removes relevant `/tmp` and `/dev/shm` artifacts.
- Removes temporary runtime state.
- Removes server logs.

Run the destructive reset only on a host dedicated to this deployment:

```shell
bash scripts/stop.sh --reset
```

### Logs

Main runtime log:

```shell
tail -f server.log
tail -n 200 server.log
head -n 100 server.log
```

Warmup logs:

```shell
tail -f logs/warmup.log
tail -f logs/warmup.server.log
```

The host scripts append server output to `server.log`. During warmup, noisy
server output is also captured in `logs/warmup.server.log`, while the
foreground tail stays focused on warmup status.

### Hugging Face uploads

Host deployment can push locally exported checkpoints:

```shell
export HF_TOKEN="<HF_WRITE_TOKEN>"
export HF_PUSH_REPO_ID="<OWNER>/<REPOSITORY>"
export HF_PUSH_PRIVATE=1

bash scripts/main.sh \
  --engine vllm \
  --model <BASE_MODEL> \
  --quantization compressed-tensors \
  --push
```

Replace `<HF_WRITE_TOKEN>` with a Hugging Face token that can write to
`<OWNER>/<REPOSITORY>`.

TensorRT Model Optimizer exports use the same checkpoint upload path:

```shell
bash scripts/main.sh \
  --model <BASE_MODEL> \
  --quantization int4_awq \
  --push
```

Rules:

- `--push` uploads locally exported weights, tokenizer assets, provenance,
  and model-card metadata.
- vLLM uploads accept only locally produced `compressed-tensors` exports.
- TensorRT-LLM uploads support all three configured ModelOpt formats.
- `HF_TOKEN` must have write access.
- Quantized export pushes require `HF_PUSH_REPO_ID`.
- `HF_PUSH_PRIVATE` defaults to `1`. Set it to `0` for a public repository.

## WebSocket API: `/ws`

### Authentication

The server accepts API keys only through headers:

```text
X-API-Key: <API_KEY>
Authorization: Bearer <API_KEY>
```

The server does not accept authentication through query parameters. The
bundled clients send `X-API-Key`.

The service has no browser-client contract and does not use `Origin` as a
security boundary. API-key authentication remains mandatory.

### Protocol rules

Every client message follows these rules:

- Use a JSON object.
- Put `type`, `v`, and message fields at the top level.
- Use nested values only for the documented `sampling` object and `history`
  list.
- Do not add an envelope wrapper.
- Do not include unknown fields.
- Set `v` to the configured protocol version, which defaults to `1`.
- Keep the encoded frame below `WEBSOCKET_MAX_MESSAGE_BYTES`.

Supported client frame types:

```text
start, message, cancel, ping, pong, end
```

Supported server frame types:

```text
token, final, done, cancelled, error, pong
```

### Connection lifecycle

1. The client opens `ws://<HOST>:8000/ws` with authentication headers.
1. The server authenticates the client and checks connection capacity.
1. The server accepts the socket and starts the idle watchdog.
1. The client sends one `start` frame.
1. The server validates the gender/personality profile, prompt, sampling values, and imported
   history.
1. The server returns `{"type":"done","status":200}` after session bootstrap.
1. The client sends `message` frames for generation turns.
1. The server streams `token`, `final`, and `done` frames.
1. The client sends `end` to close the session cleanly.

Sending `start` more than once is invalid. Use `message` for later turns.

### Start frame

`start` initializes a session but does not generate a model response by itself.

```json
{
    "type": "start",
    "v": 1,
    "gender": "female",
    "personality": "flirty",
    "prompt": "You are concise and conversational.",
    "history": [
        { "role": "user", "content": "previous message" },
        { "role": "assistant", "content": "previous reply" }
    ],
    "sampling": {
        "temperature": 0.8,
        "top_p": 0.95
    }
}
```

Fields:

| Field         | Required | Description                                                                         |
| ------------- | -------- | ----------------------------------------------------------------------------------- |
| `type`        | Yes      | Must be `start`.                                                                    |
| `v`           | Yes      | Protocol version.                                                                   |
| `gender`      | Yes      | Profile gender. Must normalize to `female` or `male`.                               |
| `personality` | Yes      | Letters-only profile value, normalized to lowercase and limited to `20` characters. |
| `prompt`      | Yes      | Full system prompt. Limited by `PROMPT_MAX_TOKENS`.                                 |
| `history`     | No       | Ordered `{role, content}` messages. Roles must be `user` or `assistant`.            |
| `sampling`    | No       | Per-session sampling overrides.                                                     |

Successful bootstrap response:

```json
{ "type": "done", "status": 200 }
```

### Message frame

`message` starts a generation turn inside an existing session.

```json
{
    "type": "message",
    "v": 1,
    "user_utterance": "answer in one sentence",
    "sampling": {
        "temperature": 0.7
    }
}
```

Fields:

| Field            | Required | Description                                  |
| ---------------- | -------- | -------------------------------------------- |
| `type`           | Yes      | Must be `message`.                           |
| `v`              | Yes      | Protocol version.                            |
| `user_utterance` | Yes      | Current user text.                           |
| `sampling`       | No       | Overrides for this and later session config. |

If generation is already running, a new `message` aborts the previous request.
The server then starts the new turn. This is the implicit barge-in path.

### Streaming frames

Normal generation:

```text
{ "type": "token", "text": "partial " }
{ "type": "token", "text": "text" }
{ "type": "final", "status": 200, "text": "partial text" }
{ "type": "done", "status": 200 }
```

The `final` text contains the accumulated visible response. The server commits
visible response text to session history. This includes partial text when an
interruption stops a send after the client has received output.

### Cancel frame

```json
{ "type": "cancel", "v": 1 }
```

The server:

- Aborts active session requests.
- Cancels the tracked asyncio task.
- Aborts the engine request.
- Sends a confirmation.

```json
{ "type": "cancelled" }
```

### Ping, pong, and end

Heartbeat:

```json
{ "type": "ping", "v": 1 }
```

Response:

```json
{ "type": "pong" }
```

Graceful close:

```json
{ "type": "end", "v": 1 }
```

Response:

```json
{ "type": "done", "status": 200 }
```

The server then closes with code `1000`.

### Error frames

All protocol errors use this shape:

```json
{
    "type": "error",
    "status": 400,
    "code": "invalid_message",
    "message": "Message must be valid JSON."
}
```

Common codes:

| Code                    | Status | Typical cause                                                  |
| ----------------------- | ------ | -------------------------------------------------------------- |
| `authentication_failed` | `401`  | Missing or invalid API key.                                    |
| `server_at_capacity`    | `503`  | `MAX_CONCURRENT_CONNECTIONS` reached.                          |
| `invalid_message`       | `400`  | Bad JSON, missing `type`, wrong version, unsupported sequence. |
| `invalid_payload`       | `400`  | Required field missing or malformed.                           |
| `invalid_settings`      | `400`  | Session prompt or profile settings invalid.                    |
| `rate_limited`          | `429`  | Message or cancel limit exceeded.                              |
| `text_too_long`         | `400`  | Prompt/history/user input cannot fit configured budgets.       |
| `internal_error`        | `500`  | Unexpected runtime failure.                                    |

### Node.js client

This example assumes that you installed the `ws` package and set `API_KEY` in
the process environment:

```javascript
import WebSocket from 'ws';

const apiKey = process.env.API_KEY;
if (!apiKey) {
    throw new Error('API_KEY is required');
}

const ws = new WebSocket('ws://127.0.0.1:8000/ws', {
    headers: { 'X-API-Key': apiKey },
});

let sessionStarted = false;

ws.on('open', () => {
    ws.send(
        JSON.stringify({
            type: 'start',
            v: 1,
            gender: 'female',
            personality: 'flirty',
            prompt: 'You are concise.',
            history: [],
        }),
    );
});

ws.on('message', (raw) => {
    const frame = JSON.parse(raw.toString());

    if (!sessionStarted && frame.type === 'done' && frame.status === 200) {
        sessionStarted = true;
        ws.send(
            JSON.stringify({
                type: 'message',
                v: 1,
                user_utterance: 'say hello in one sentence',
            }),
        );
        return;
    }

    if (frame.type === 'token') {
        process.stdout.write(frame.text);
    }

    if (frame.type === 'error') {
        console.error(frame);
        ws.close();
        return;
    }

    if (sessionStarted && frame.type === 'done') {
        process.stdout.write('\n');
        ws.close();
    }
});
```

## Prompt, history, and sampling

### Profile bootstrap

The client provides the complete prompt in `start`. The server validates and
stores these session fields:

- Profile gender in `gender`.
- Profile value in `personality`.
- System prompt in `prompt`.
- Imported conversation turns in `history`.
- Optional sampling overrides.

The server renders the prompt through the deployed model tokenizer template.
Prompt rendering fails for a model without a usable chat template. The runtime
does not synthesize a replacement template.

### History import

History must be an ordered list:

```json
[
    { "role": "user", "content": "first user message" },
    { "role": "assistant", "content": "first assistant reply" }
]
```

Accepted roles:

- `user`
- `assistant`

History handling:

- The server normalizes roles to lowercase.
- The server rejects unknown fields.
- The server can merge consecutive user entries.
- The server trims old complete turns when a session exceeds the token budgets.
- The server appends completed generated turns to session history.

### Prompt fitting

Prompt fitting happens before generation. The server fits these inputs into the
model sequence budget:

1. Static profile prompt.
1. Retained history.
1. Current user utterance.
1. Configured output budget.
1. Buffer tokens.

When a turn is too large, the server drops older history first. It trims the
current user text only when removing history does not make enough room.

### Sampling overrides

Pass sampling values in a nested object:

```json
{
    "type": "message",
    "v": 1,
    "user_utterance": "try a warmer tone",
    "sampling": {
        "temperature": 0.9,
        "top_p": 0.9,
        "presence_penalty": 0.2,
        "sanitize_output": true
    }
}
```

Pass them at the top level instead:

```json
{
    "type": "message",
    "v": 1,
    "user_utterance": "be deterministic",
    "temperature": 0.0
}
```

Supported override keys:

- `temperature`
- `top_p`
- `top_k`
- `min_p`
- `repetition_penalty`
- `presence_penalty`
- `frequency_penalty`
- `sanitize_output`

Numeric fields accept numbers or numeric strings. Boolean values are not valid
numeric inputs. `sanitize_output` accepts only a boolean and defaults to
disabled.

If the same sampling key appears at the top level and inside `sampling`, the
nested value wins.

## Inference engines

### Engine selection

Host scripts accept one exact engine flag:

```shell
bash scripts/main.sh --model <MODEL>
bash scripts/main.sh --engine vllm --model <MODEL>
```

The host workflow persists source identity, resolved checkpoint, detected
runtime format, and requested export format separately. Lower-level runtime
state includes:

```shell
export INFERENCE_ENGINE=trt
export MODEL="<REPOSITORY_OR_PATH>"
export RUNTIME_QUANTIZATION=int4_awq
```

### TensorRT-LLM runtime

TensorRT-LLM `1.3.0rc20` is the default host engine. The public PyTorch backend
loads ModelOpt checkpoints in Hugging Face layout and enables KV-cache block
reuse.

The runtime uses one GPU with tensor parallelism set to `1`. It does not compile
or download serialized TensorRT engine directories.

Runtime settings are:

| Variable              | Default    | Description                                                             |
| --------------------- | ---------- | ----------------------------------------------------------------------- |
| `TRT_MAX_BATCH_SIZE`  | `64`       | Sets the maximum number of sequences the runtime can schedule together. |
| `TRT_DTYPE`           | `auto`     | Selects `auto`, `float16`, `bfloat16`, or `float32`.                    |
| `GPU_MEMORY_FRACTION` | `0.90`     | Sets the free-memory fraction available to the TensorRT KV cache.       |
| `KV_DTYPE`            | GPU policy | Selects `auto` or `fp8` KV-cache storage.                               |

`TRT_MAX_BATCH_SIZE` is not the same thing as `MAX_CONCURRENT_CONNECTIONS`.

- `TRT_MAX_BATCH_SIZE` controls TensorRT runtime scheduling capacity.
- `MAX_CONCURRENT_CONNECTIONS` controls WebSocket admission.

A batch limit of `64` is a scheduling ceiling. Actual concurrency depends on
KV-cache memory and the sequence length of active requests.

### vLLM runtime

Select vLLM with `--engine vllm`. vLLM provides
dynamic serving with model-supported prefix caching and runtime cache reset
support.

The runtime is text-only and uses one GPU with tensor parallelism set to `1`.

Relevant variables:

| Variable                       | Default    | Description                        |
| ------------------------------ | ---------- | ---------------------------------- |
| `GPU_MEMORY_FRACTION`          | `0.90`     | GPU memory fraction used by vLLM.  |
| `KV_DTYPE`                     | GPU policy | KV cache dtype preference.         |
| `CACHE_RESET_INTERVAL_SECONDS` | `600`      | Periodic prefix-cache reset timer. |

vLLM derives its runtime policy from the loaded model and GPU. This includes:

- Compute dtype.
- Attention backend.
- Scheduler limits.
- Chunked prefill support.
- Prefix-caching support.

Hybrid models use vLLM's native cache policy.

The server attempts a non-preemptive vLLM prefix-cache reset every ten minutes.
It never resets while another client remains because of a disconnect. The last
disconnect bypasses the timer and attempts the same non-preemptive reset
immediately. When the engine declines a reset because active requests still own
cache entries, the server retries the reset after a fixed 30 seconds. The server
cancels and awaits the daemon before engine shutdown. TensorRT-LLM does not use
this coordinator because its runtime relies on block reuse.

## Quantization

### Detection

Quantization is explicitly opt-in through `--quantization FORMAT`. The pipeline
does not inspect model names, select a default format, use a synthetic
unquantized value, or accept aliases. Without a request it deploys the source
unchanged. With a request it exports only an unquantized source. If the source
is already quantized, deployment reports the detected format and instructs the
operator to omit `--quantization`; re-quantization is not supported.

For vLLM, prequantized checkpoints must declare a supported runtime format.
Qwen 3.5 MoE with Generative Pre-trained Transformer Quantization (GPTQ) selects
`moe_wna16` from model configuration. ModelOpt NVFP4 selects `modelopt_fp4`.

For TensorRT-LLM, the host pipeline reads the ModelOpt unified metadata. A
prequantized checkpoint must declare `quant_method: modelopt` and a supported
`quant_algo`. The host pipeline exports an unquantized source locally only when
you request an export; otherwise, TensorRT-LLM serves the source unchanged.
Conflicting, unsupported, or malformed metadata stops deployment.

Detection checks `config.json`, `quantization_config.json`,
`quant_config.json`, and `awq_config.json`. Conflicting declarations across
those files stop deployment.

### Supported formats

| Backend      | Formats                                             |
| ------------ | --------------------------------------------------- |
| vLLM         | `awq`, `gptq`, `compressed-tensors`, `fp8`, `nvfp4` |
| TensorRT-LLM | `int4_awq`, `nvfp4`, `fp8`                          |

### vLLM quantization

The vLLM path supports:

- Existing Activation-aware Weight Quantization (AWQ) and GPTQ checkpoints that
  declare the requested format.
- Existing compressed-tensors and FP8 checkpoints.
- ModelOpt `NVFP4` and `W4A16_NVFP4` checkpoints through `modelopt_fp4`.
- Compressed-tensors NVFP4 checkpoints as `compressed-tensors` artifacts.
- INT8 W8A8 and SmoothQuant compressed-tensors checkpoints on supported GPUs.
- Fresh compressed-tensors W4A16 exports through LLM Compressor `0.12`.
- Online vLLM FP8 for an unquantized source selected with `fp8`.

On an `sm80` A100, vLLM can serve a compatible W8A8 INT8 or SmoothQuant
checkpoint. The repository identifies that artifact as `compressed-tensors`,
and `int8_sq` is not a vLLM runtime format.

Calibration defaults:

| Variable                           | Default         | Description                              |
| ---------------------------------- | --------------- | ---------------------------------------- |
| `VLLM_CALIBRATION_DATASET`         | `open_platypus` | Registered LLM Compressor dataset.       |
| `VLLM_CALIBRATION_SAMPLES`         | `256`           | Number of calibration samples.           |
| `VLLM_CALIBRATION_SEQUENCE_LENGTH` | `512`           | Maximum calibration sequence length.     |
| `VLLM_CALIBRATION_BATCH_SIZE`      | `1`             | Calibration batch size.                  |
| `VLLM_CALIBRATION_PIPELINE`        | `independent`   | `basic`, `independent`, or `sequential`. |

Dense checkpoints use asymmetric W4A16 with dual scaling.

Supported Qwen 3 MoE layouts use symmetric W4A16 and all-expert calibration.
The Qwen 3 Next policy also leaves `shared_expert_gate` unquantized.

The local exporter rejects other MoE model types until the repository defines a
pinned architecture-specific recipe. Recipe selection never uses the
repository name.

### TensorRT-LLM quantization

Host TensorRT quantization uses NVIDIA Model Optimizer `0.45.0`:

1. Use a current ModelOpt unified checkpoint or export one locally.
1. Load the checkpoint directly with the public PyTorch backend.

The exporter runs in the separate quantization environment. TensorRT-LLM keeps
its required Model Optimizer `0.37.0` runtime dependency in the serving
environment.

ModelOpt `int8_sq` is not offered on this backend because ModelOpt exports it
without the unified Hugging Face schema consumed by the public PyTorch runtime.

Every unquantized TensorRT input produces or reuses an export whose provenance
matches the exact source commit and calibration request.

The repository accepts NVFP4 on Blackwell and FP8 on Ada or Hopper. It accepts
INT4-AWQ on its supported Ampere, Ada, Hopper, and Blackwell architectures.

Calibration settings are:

| Variable                          | Default         | Description                                            |
| --------------------------------- | --------------- | ------------------------------------------------------ |
| `TRT_AWQ_BLOCK_SIZE`              | `128`           | Sets the ModelOpt AWQ group size.                      |
| `TRT_CALIBRATION_DATASET`         | `cnn_dailymail` | Selects the ModelOpt calibration dataset.              |
| `TRT_CALIBRATION_SAMPLES`         | `64`            | Sets the calibration sample count.                     |
| `TRT_CALIBRATION_SEQUENCE_LENGTH` | `512`           | Sets the maximum calibration sequence length.          |
| `TRT_CALIBRATION_MEMORY_FRACTION` | `0.8`           | Limits GPU memory used while placing the source model. |
| `TRT_SEQUENTIAL_DEVICE_MAP`       | `0`             | Enables sequential device placement when set to `1`.   |

Model Optimizer retains ownership of calibration batch sizing. The repository
does not pass `--batch_size`.

The TensorRT allowlists include Qwen 3.5 and Gemma 4 sources for export with
the pinned Model Optimizer `0.45.0`. A model remains usable only when ModelOpt
can export the requested format and the target GPU can run it.

### Calibration memory

The exporters apply the configured defaults. They do not search for settings
that fit the current GPU automatically.

If vLLM calibration runs out of memory:

1. Lower `VLLM_CALIBRATION_BATCH_SIZE`.
1. Lower `VLLM_CALIBRATION_SEQUENCE_LENGTH` if the batch size is already `1`.
1. Lower `VLLM_CALIBRATION_SAMPLES` only when a smaller calibration set is acceptable.

If TensorRT calibration runs out of memory:

1. Set `TRT_SEQUENTIAL_DEVICE_MAP=1`.
1. Lower `TRT_CALIBRATION_MEMORY_FRACTION` to leave more placement headroom.
1. Lower `TRT_CALIBRATION_SEQUENCE_LENGTH`.
1. Lower `TRT_CALIBRATION_SAMPLES` only when a smaller calibration set is acceptable.

Sequence length and batch size have the strongest effect on peak calibration
memory. Sample count primarily affects calibration coverage and duration.
Every change becomes part of the checkpoint cache identity.

### Quantization provenance and publishing

Locally exported checkpoints contain `quantization_metadata.json`. The file
records:

- Immutable source revision or local source fingerprint.
- Quantizer version and pinned revision.
- Selected recipe and calibration inputs.
- Exported checkpoint `quantization_config`.
- Quantization GPU and SM architecture.
- CUDA and Python versions.
- Creation time.

The export preserves tokenizer and custom-code assets from the immutable source.
Local validation checks those assets before the repository accepts or publishes
the checkpoint.

Cache reuse requires the source identity and every output-affecting setting to
match. `QUANT_FORCE_REBUILD=1` bypasses the match. `--push` can publish
either a newly generated or valid reused export and regenerates the detailed
model card before upload.

Publishing inherits the source license when Hugging Face exposes it. If the
license lookup fails or the source does not declare one, the generated model
card uses `other` and links back to the source.

Execution-environment fields are provenance only. They do not make a portable
checkpoint specific to the GPU that produced it.

## Docker images

The [Docker image guide](docker/README.md) owns the complete build contract.
Each image contains one engine and one model snapshot selected by an immutable
40-character Hugging Face commit SHA.

Docker builds do not run the host quantization pipelines. They bake `MODEL`
unchanged, detect any existing checkpoint format during validation and runtime,
and fail only when that format is incompatible with the selected backend.
Unquantized models remain unquantized in both image stacks.

Run either image with the required runtime values:

```shell
docker run --gpus all --detach \
  --name text-inference \
  --env API_KEY="<API_KEY>" \
  --env MAX_CONCURRENT_CONNECTIONS=8 \
  --publish 8000:8000 \
  <IMAGE> [--logs]
```

Running the image publishes only the public WebSocket port. The fixed loopback
probe port is not exposed to the host.

`pyproject.toml` declares the engine extras, and `uv.lock` pins the resolved
dependencies. Docker and host installation use those same lock inputs.

After dependency edits:

```shell
mise run deps
mise run deps:verify
```

## Telemetry

Telemetry is optional. When credentials are absent, the server keeps local
metrics objects but does not configure remote exporters.

### Enable backends

| Backend             | Enable by setting | Result                                                |
| ------------------- | ----------------- | ----------------------------------------------------- |
| Sentry              | `SENTRY_DSN`      | Error capture with contextual tags and rate limiting. |
| Axiom/OpenTelemetry | `AXIOM_API_TOKEN` | Traces and metrics exported through OTLP/HTTP.        |

### Telemetry environment

| Variable                                    | Default                           | Description                       |
| ------------------------------------------- | --------------------------------- | --------------------------------- |
| `SENTRY_DSN`                                | None                              | Enables Sentry when set.          |
| `SENTRY_ENVIRONMENT`                        | `production`                      | Sentry environment tag.           |
| `SENTRY_RELEASE`                            | None                              | Sentry release tag.               |
| `SENTRY_SAMPLE_RATE`                        | `1.0`                             | Sentry error sample rate.         |
| `AXIOM_API_TOKEN`                           | None                              | Enables Axiom/OTel when set.      |
| `AXIOM_DATASET`                             | `text-inference-api`              | Axiom dataset.                    |
| `AXIOM_ENVIRONMENT`                         | `production`                      | Deployment environment tag.       |
| `AXIOM_TRACES_ENDPOINT`                     | `https://api.axiom.co/v1/traces`  | Trace endpoint.                   |
| `AXIOM_METRICS_ENDPOINT`                    | `https://api.axiom.co/v1/metrics` | Metric endpoint.                  |
| `CLOUD_PLATFORM`                            | None                              | Optional deployment platform tag. |
| `OTEL_RESOURCE_NAME`                        | `text-inference-api`              | Service resource name.            |
| `OTEL_TRACES_EXPORT_INTERVAL_MILLISECONDS`  | `5000`                            | Span export interval.             |
| `OTEL_METRICS_EXPORT_INTERVAL_MILLISECONDS` | `15000`                           | Metric export interval.           |
| `OTEL_TRACES_BATCH_SIZE`                    | `512`                             | Max spans per export batch.       |

### Spans

| Span                        | Meaning                 |
| --------------------------- | ----------------------- |
| `text_inference.session`    | WebSocket session.      |
| `text_inference.request`    | One generation request. |
| `text_inference.generation` | Engine generation span. |

### Histograms

| Metric                                     | Unit        | Description                    |
| ------------------------------------------ | ----------- | ------------------------------ |
| `text_inference.ttft`                      | `s`         | Time to first token.           |
| `text_inference.request_latency`           | `s`         | End-to-end request latency.    |
| `text_inference.token_latency`             | `s`         | Inter-token arrival time.      |
| `text_inference.connection_duration`       | `s`         | WebSocket session duration.    |
| `text_inference.connection_semaphore_wait` | `s`         | Slot acquisition wait.         |
| `text_inference.prompt_tokens`             | `{token}`   | Input prompt token count.      |
| `text_inference.completion_tokens`         | `{token}`   | Output completion token count. |
| `text_inference.generations_per_session`   | `{request}` | Requests per session.          |
| `text_inference.startup_duration`          | `s`         | Server startup time.           |
| `text_inference.phase_latency`             | `s`         | Latency by execution phase.    |
| `text_inference.ws_send_latency`           | `s`         | WebSocket frame send latency.  |

### Counters

| Metric                                        | Unit           | Description                          |
| --------------------------------------------- | -------------- | ------------------------------------ |
| `text_inference.requests_total`               | `{request}`    | Total requests.                      |
| `text_inference.tokens_generated_total`       | `{token}`      | Total tokens generated.              |
| `text_inference.prompt_tokens_total`          | `{token}`      | Total prompt tokens processed.       |
| `text_inference.connections_rejected_total`   | `{connection}` | Connections rejected at capacity.    |
| `text_inference.session_churn_total`          | `{session}`    | Completed sessions.                  |
| `text_inference.cancellation_total`           | `{request}`    | Client cancellations.                |
| `text_inference.errors_total`                 | `{error}`      | Unhandled errors.                    |
| `text_inference.timeout_disconnects_total`    | `{connection}` | Idle timeout disconnects.            |
| `text_inference.rate_limit_violations_total`  | `{violation}`  | Rate limit hits.                     |
| `text_inference.cache_resets_total`           | `{reset}`      | vLLM cache resets.                   |
| `text_inference.cache_reset_skips_total`      | `{skip}`       | Declined or skipped cache resets.    |
| `text_inference.cache_reset_failures_total`   | `{failure}`    | Failed cache reset attempts.         |
| `text_inference.phase_errors_total`           | `{error}`      | Errors grouped by execution phase.   |
| `text_inference.disconnect_mid_stream_total`  | `{disconnect}` | Client disconnects during send.      |
| `text_inference.early_cancel_total`           | `{cancel}`     | Cancellations before first token.    |
| `text_inference.empty_model_output_total`     | `{output}`     | Generations that produced no output. |
| `text_inference.engine_abort_retryable_total` | `{abort}`      | Retryable engine abort calls.        |

### Up-down counters

| Metric                              | Unit           | Description                    |
| ----------------------------------- | -------------- | ------------------------------ |
| `text_inference.active_connections` | `{connection}` | Current WebSocket connections. |
| `text_inference.active_generations` | `{generation}` | Current running generations.   |

### GPU observables

| Metric                            | Unit | Description           |
| --------------------------------- | ---- | --------------------- |
| `text_inference.gpu.memory_used`  | `By` | GPU memory in use.    |
| `text_inference.gpu.memory_free`  | `By` | GPU memory available. |
| `text_inference.gpu.memory_total` | `By` | Total GPU memory.     |
| `text_inference.gpu.utilization`  | `%`  | GPU utilization.      |

GPU observations include `gpu.device.id`. CPU-only environments do not emit
GPU observations.

## Logging

`APPLICATION_LOG_LEVEL` controls the root and application logger levels. The default is
`INFO`.

The server uses one fixed log format, so every record carries the same context:

```text
%(levelname)s %(asctime)s name=%(name)s session_id=%(session_id)s request_id=%(request_id)s client_id=%(client_id)s msg=%(message)s
```

Use these commands to inspect host logs:

```shell
tail -f server.log
tail -n 200 server.log
tail -f logs/warmup.log
```

Default terminal output contains only repository-owned Bash and Python logs.
The output layer quiets dependency loggers, warnings, progress bars,
subprocesses, and native standard streams from the model, quantization, CUDA,
and engine stacks. Raw server diagnostics still append to `server.log`, and
warmup diagnostics also remain in the detailed warmup capture.

Pass `--logs` to deploy, restart, warmup, or a Docker entrypoint to disable
suppression before GPU-library imports and stream raw output. On failure, the
repository prints a concise error and the detailed log path.

## Health checks

The process owns two loopback-only probe routes:

```text
GET http://127.0.0.1:8001/healthz
GET http://127.0.0.1:8001/readyz
```

Check them locally with the fixed two-second helper or curl:

```shell
bash scripts/readiness.sh
curl --fail --max-time 2 http://127.0.0.1:8001/healthz
curl --fail --max-time 2 http://127.0.0.1:8001/readyz
```

`/healthz` reports that the process event loop is alive. `/readyz` returns 503
until the server initializes dependencies and the public WebSocket listener
accepts connections, returns 200 while serving, and returns 503 before shutdown
draining begins. Public port 8000 has no HTTP probe routes. The application
does not expose FastAPI documentation, ReDoc, or OpenAPI routes.

## Developer workflow

### Setup

```shell
mise run setup
```

The setup task installs tool versions, dependencies, the linters, and the Git
hooks:

- `mise install`
- `bun install --frozen-lockfile`
- `bunx --no-install gspot install`
- `mise run deps`

### Dependency commands

```shell
mise run deps
mise run deps:verify
```

`mise run deps` synchronizes the Python dependencies with `uv`, including the
`local` extra that the type checker and the tests read. It also installs Bun
dependencies from the frozen lockfile. Run it again after `gspot install`,
which synchronizes `.venv` without extras.

`mise run deps:verify` checks:

- `uv.lock` is current.
- Frozen `uv sync` succeeds.
- The Bun lockfile installation is stable.

### Lint and format

gspot runs the linters, formatters, type checker, and security scanners from
one settings file, `gspot.toml`:

```shell
bunx --no-install gspot check --fix
bunx --no-install gspot check
```

The Git hooks run the same checks before each commit and push.

`gspot.toml` also holds the import rules. Each `[[import_rule]]` record names one
layer of the code and lists exactly the layers it may import.

### Tests

```shell
mise run test
mise run test:unit
mise run test:integration
mise run test:integration:cancel
mise run test:integration:idle
mise run test:integration:sanitizer
```

`test` runs the unit and in-process integration suites. Task arguments pass
through after `--`.

## Test clients

All five end-to-end clients accept the same connection options:

- `--server` accepts local `ws://` and remote `wss://` WebSocket URLs.
- `--api-key` defaults to `API_KEY`.
- `--timeout` bounds one complete transaction or turn and defaults to 120
  seconds.
- `--sanitize` opts into server output sanitization. Omission sends no override
  and leaves output unsanitized.

The corresponding shared environment values are:

| Variable                               | Default                  | Description                        |
| -------------------------------------- | ------------------------ | ---------------------------------- |
| `SERVER_URL`                           | `ws://127.0.0.1:8000/ws` | Target server.                     |
| `API_KEY`                              | None                     | Required authentication key.       |
| `GENDER`                               | `female`                 | Default client prompt gender.      |
| `PERSONALITY`                          | `flirty`                 | Default client prompt personality. |
| `TEST_WEBSOCKET_PING_INTERVAL_SECONDS` | `20`                     | Client ping interval.              |
| `TEST_WEBSOCKET_PING_TIMEOUT_SECONDS`  | `20`                     | Client ping timeout.               |

Run every finite noninteractive client, excluding live:

```shell
mise run test:e2e -- --server wss://<HOST>/ws --api-key <API_KEY>
```

### Warmup client

```shell
mise run test:e2e:warmup -- "who was Columbus?"
mise run test:e2e:warmup -- \
  --gender male \
  --personality flirty \
  "hello"
mise run test:e2e:warmup -- --double-ttfb "say hi"
```

Reports:

- Time to first token.
- Time to first three words.
- Total latency.
- Stream latency.
- Chunk count.
- Response character count.

### Benchmark client

```shell
mise run test:e2e:bench -- --requests 32 --concurrency 8
mise run test:e2e:bench -- --timeout 180 -r 100 -c 20
mise run test:e2e:bench -- --double-ttfb -r 16 -c 4
```

Benchmark mode reports percentile summaries. It also reports sessions rejected
when concurrency exceeds `MAX_CONCURRENT_CONNECTIONS`.

### Conversation client

```shell
mise run test:e2e:conversation
mise run test:e2e:conversation -- \
  --server ws://127.0.0.1:8000/ws
mise run test:e2e:conversation -- \
  --temperature 0.8 \
  --top-p 0.9
```

The client runs a scripted multi-turn conversation. It checks retained history
and steady-state latency.

### History recall client

```shell
mise run test:e2e:history
mise run test:e2e:history -- \
  --gender male \
  --personality flirty
mise run test:e2e:history -- \
  --temperature 0.8 \
  --top-p 0.9
```

### Interactive live client

```shell
mise run test:e2e:live -- --gender female --personality flirty
mise run test:e2e:live -- --gender male --personality warm
mise run test:e2e:live -- --timeout 120 "start with a greeting"
```

The live profile registry uses the exact `(gender, personality)` pair as its key.
Its commands are `/help`, `/history`, `/genders`, `/personalities`, `/stats`,
and `/stop`. `/stats` takes no arguments and toggles metrics logging.

### Focused pytest targets

```shell
mise run test:unit
mise run test:integration
mise run test:unit -- tests/suites/unit/websocket
mise run test:unit -- tests/suites/unit/history
mise run test:unit -- tests/suites/unit/quantization
```

Integration tests include WebSocket cancel/recovery and idle-timeout behavior.

## Troubleshooting

### `authentication_failed`

Check that the client sends one of:

```text
X-API-Key: <API_KEY>
Authorization: Bearer <API_KEY>
```

If one client host has sent repeated invalid credentials, wait for the
authentication throttle window to expire before retrying.

### `server_at_capacity`

The server rejected the socket because the number of admitted connections
reached `MAX_CONCURRENT_CONNECTIONS`. Increase the setting or retry with backoff.

### `rate_limited`

The client exceeded `WEBSOCKET_MESSAGES_PER_WINDOW` or
`WEBSOCKET_CANCELS_PER_WINDOW` within `WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS`.
Reduce the request rate or raise the relevant limit.

### `start may only be sent once`

The socket already has a session. Send `message` for later turns. Open a new
connection when the client needs a separate session.

### `no active session; send start first`

The client sent `message` before a successful `start`. Bootstrap the session
and wait for `{"type":"done","status":200}` before sending a turn.

### Quantization detection fails

An existing checkpoint format must be compatible with the selected engine. To
serve a prequantized checkpoint unchanged, omit `--quantization`:

```shell
bash scripts/main.sh --engine vllm --model <AWQ_MODEL>
bash scripts/main.sh --model <MODELOPT_FP8_MODEL>
```

Use `--quantization FORMAT` only with an unquantized source. Deployment rejects
re-quantization of an already-quantized source.

### Calibration runs out of memory

The exporters do not auto-tune calibration for the current GPU. Apply the
engine-specific controls in [calibration memory](#calibration-memory), then
retry the deployment.

Changing a calibration setting changes the checkpoint cache identity. The next
run rebuilds the checkpoint unless an export with the new settings already
exists.

### Tokenizer files are missing

Local model paths must include tokenizer assets such as:

- `tokenizer.json`
- `tokenizer_config.json`
- `tokenizer.model`
- `vocab.json`
- `merges.txt`

Deployment fails before serving when tokenizer validation cannot find usable
files.

### The TensorRT checkpoint is invalid

For a local TensorRT checkpoint:

```shell
bash scripts/main.sh --model <MODELOPT_CHECKPOINT_PATH>
```

The directory must contain `config.json`, tokenizer assets, and safetensors
weights. Its `config.json` must use the Model Optimizer unified
`quantization_config` schema. Compiled TensorRT engine files are not runtime
inputs for this backend.

### The required CUDA 13.1 support is unavailable

Host TensorRT-LLM deployment expects CUDA 13.1 or later. The scripts validate
the toolkit and driver capability.

If detection fails:

- Ensure `nvcc` is on `PATH`.
- Ensure the NVIDIA driver supports CUDA 13.1 or later.
- Confirm that `nvidia-smi` detects the target GPU.

### Docker build rejects the revision

Docker remote downloads require 40-character Hugging Face commit SHAs:

```shell
MODEL_REVISION="<40_CHARACTER_COMMIT_SHA>"
```

This prevents mutable image inputs.

### Dependency lock is stale

Run:

```shell
mise run deps
mise run deps:verify
```

### Readiness probe fails

The probe listener is intentionally loopback-only. Run `bash scripts/readiness.sh`
on the host or with `docker exec` inside the container, then inspect the detailed
server log if readiness remains unavailable.

### Server starts but the client hangs

Check:

```shell
tail -n 200 server.log
bash scripts/readiness.sh
```

Then verify:

- Both the server and the client have a value for `API_KEY`.
- The client sends `start` before `message`.
- The prompt and history fit the configured token budgets.
- The engine completed startup without an error in `server.log`.
- `MAX_CONCURRENT_CONNECTIONS` still has admission capacity.
