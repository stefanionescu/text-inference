"""Telemetry environment values, metric specifications, spans, and Sentry constants."""

# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------
SENTRY_DSN: str | None = None
SENTRY_ENVIRONMENT = "production"
SENTRY_RELEASE: str | None = None
SENTRY_SAMPLE_RATE = 1.0

# ---------------------------------------------------------------------------
# Axiom / OTel
# ---------------------------------------------------------------------------
AXIOM_API_TOKEN: str | None = None
AXIOM_DATASET = "text-inference-api"
AXIOM_ENVIRONMENT = "production"
AXIOM_TRACES_ENDPOINT = "https://api.axiom.co/v1/traces"
AXIOM_METRICS_ENDPOINT = "https://api.axiom.co/v1/metrics"
# ---------------------------------------------------------------------------
# OTel tuning
# ---------------------------------------------------------------------------
OTEL_RESOURCE_NAME = "text-inference-api"
OTEL_TRACES_EXPORT_INTERVAL_MILLISECONDS = 5000
OTEL_METRICS_EXPORT_INTERVAL_MILLISECONDS = 15000
OTEL_TRACES_BATCH_SIZE = 512

# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------
CLOUD_PLATFORM: str | None = None

# ---------------------------------------------------------------------------
# Metric spec tuples: (name, unit, description)
# ---------------------------------------------------------------------------

# Histograms
METRIC_TTFT = ("text_inference.ttft", "s", "Time to first token")
METRIC_REQUEST_LATENCY = ("text_inference.request_latency", "s", "End-to-end request latency")
METRIC_TOKEN_LATENCY = ("text_inference.token_latency", "s", "Inter-token arrival time")
METRIC_CONNECTION_DURATION = ("text_inference.connection_duration", "s", "WebSocket session duration")
METRIC_CONNECTION_SEMAPHORE_WAIT = ("text_inference.connection_semaphore_wait", "s", "Slot acquisition wait")
METRIC_PROMPT_TOKENS = ("text_inference.prompt_tokens", "{token}", "Input prompt token count")
METRIC_COMPLETION_TOKENS = ("text_inference.completion_tokens", "{token}", "Output completion token count")
METRIC_GENERATIONS_PER_SESSION = (
    "text_inference.generations_per_session",
    "{request}",
    "Requests per session",
)
METRIC_STARTUP_DURATION = ("text_inference.startup_duration", "s", "Server startup time")
METRIC_PHASE_LATENCY = ("text_inference.phase_latency", "s", "Latency by execution phase")
METRIC_WEBSOCKET_SEND_LATENCY = ("text_inference.websocket_send_latency", "s", "WebSocket frame send latency")

# Counters
METRIC_REQUESTS_TOTAL = ("text_inference.requests_total", "{request}", "Total requests")
METRIC_TOKENS_GENERATED_TOTAL = ("text_inference.tokens_generated_total", "{token}", "Total tokens generated")
METRIC_PROMPT_TOKENS_TOTAL = ("text_inference.prompt_tokens_total", "{token}", "Total prompt tokens processed")
METRIC_CONNECTIONS_REJECTED_TOTAL = (
    "text_inference.connections_rejected_total",
    "{connection}",
    "Rejected at capacity",
)
METRIC_SESSION_CHURN_TOTAL = ("text_inference.session_churn_total", "{session}", "Completed sessions")
METRIC_CANCELLATION_TOTAL = ("text_inference.cancellation_total", "{request}", "Client cancellations")
METRIC_ERRORS_TOTAL = ("text_inference.errors_total", "{error}", "Unhandled errors")
METRIC_TIMEOUT_DISCONNECTS_TOTAL = (
    "text_inference.timeout_disconnects_total",
    "{connection}",
    "Idle timeout disconnects",
)
METRIC_RATE_LIMIT_VIOLATIONS_TOTAL = (
    "text_inference.rate_limit_violations_total",
    "{violation}",
    "Rate limit hits",
)
METRIC_CACHE_RESETS_TOTAL = ("text_inference.cache_resets_total", "{reset}", "vLLM cache resets")
METRIC_CACHE_RESET_SKIPS_TOTAL = (
    "text_inference.cache_reset_skips_total",
    "{skip}",
    "vLLM cache reset attempts skipped or declined",
)
METRIC_CACHE_RESET_FAILURES_TOTAL = (
    "text_inference.cache_reset_failures_total",
    "{failure}",
    "vLLM cache reset failures",
)
METRIC_PHASE_ERRORS_TOTAL = ("text_inference.phase_errors_total", "{error}", "Errors grouped by execution phase")
METRIC_DISCONNECT_MID_STREAM_TOTAL = (
    "text_inference.disconnect_mid_stream_total",
    "{disconnect}",
    "Client disconnects during server send",
)
METRIC_EARLY_CANCEL_TOTAL = (
    "text_inference.early_cancel_total",
    "{cancel}",
    "Cancelled generations before first token",
)
METRIC_EMPTY_MODEL_OUTPUT_TOTAL = (
    "text_inference.empty_model_output_total",
    "{output}",
    "Generations that produced no output",
)
METRIC_ENGINE_ABORT_RETRYABLE_TOTAL = (
    "text_inference.engine_abort_retryable_total",
    "{abort}",
    "Retryable abort calls issued to engine",
)

# UpDown counters
METRIC_ACTIVE_CONNECTIONS = ("text_inference.active_connections", "{connection}", "Current WebSocket connections")
METRIC_ACTIVE_GENERATIONS = ("text_inference.active_generations", "{generation}", "Currently running generations")

# GPU observables
METRIC_GPU_MEMORY_USED = ("text_inference.gpu.memory_used", "By", "GPU memory in use")
METRIC_GPU_MEMORY_FREE = ("text_inference.gpu.memory_free", "By", "GPU memory available")
METRIC_GPU_MEMORY_TOTAL = ("text_inference.gpu.memory_total", "By", "Total GPU memory")
METRIC_GPU_UTILIZATION = ("text_inference.gpu.utilization", "%", "GPU compute utilization")

# ---------------------------------------------------------------------------
# Span names
# ---------------------------------------------------------------------------
SPAN_SESSION = "text_inference.session"
SPAN_REQUEST = "text_inference.request"
SPAN_GENERATION = "text_inference.generation"

# ---------------------------------------------------------------------------
# Sentry constants
# ---------------------------------------------------------------------------
SENTRY_RATE_LIMIT_SECONDS: float = 10.0
SENTRY_TAG_SESSION_ID = "session_id"
SENTRY_TAG_REQUEST_ID = "request_id"
SENTRY_TAG_CLIENT_ID = "client_id"

__all__ = [
    "AXIOM_API_TOKEN",
    "AXIOM_DATASET",
    "AXIOM_ENVIRONMENT",
    "AXIOM_METRICS_ENDPOINT",
    "AXIOM_TRACES_ENDPOINT",
    "CLOUD_PLATFORM",
    "METRIC_ACTIVE_CONNECTIONS",
    "METRIC_ACTIVE_GENERATIONS",
    "METRIC_CACHE_RESETS_TOTAL",
    "METRIC_CACHE_RESET_FAILURES_TOTAL",
    "METRIC_CACHE_RESET_SKIPS_TOTAL",
    "METRIC_CANCELLATION_TOTAL",
    "METRIC_COMPLETION_TOKENS",
    "METRIC_CONNECTIONS_REJECTED_TOTAL",
    "METRIC_CONNECTION_DURATION",
    "METRIC_CONNECTION_SEMAPHORE_WAIT",
    "METRIC_DISCONNECT_MID_STREAM_TOTAL",
    "METRIC_EARLY_CANCEL_TOTAL",
    "METRIC_EMPTY_MODEL_OUTPUT_TOTAL",
    "METRIC_ENGINE_ABORT_RETRYABLE_TOTAL",
    "METRIC_ERRORS_TOTAL",
    "METRIC_GENERATIONS_PER_SESSION",
    "METRIC_GPU_MEMORY_FREE",
    "METRIC_GPU_MEMORY_TOTAL",
    "METRIC_GPU_MEMORY_USED",
    "METRIC_GPU_UTILIZATION",
    "METRIC_PHASE_ERRORS_TOTAL",
    "METRIC_PHASE_LATENCY",
    "METRIC_PROMPT_TOKENS",
    "METRIC_PROMPT_TOKENS_TOTAL",
    "METRIC_RATE_LIMIT_VIOLATIONS_TOTAL",
    "METRIC_REQUESTS_TOTAL",
    "METRIC_REQUEST_LATENCY",
    "METRIC_SESSION_CHURN_TOTAL",
    "METRIC_STARTUP_DURATION",
    "METRIC_TIMEOUT_DISCONNECTS_TOTAL",
    "METRIC_TOKENS_GENERATED_TOTAL",
    "METRIC_TOKEN_LATENCY",
    "METRIC_TTFT",
    "METRIC_WEBSOCKET_SEND_LATENCY",
    "OTEL_METRICS_EXPORT_INTERVAL_MILLISECONDS",
    "OTEL_RESOURCE_NAME",
    "OTEL_TRACES_BATCH_SIZE",
    "OTEL_TRACES_EXPORT_INTERVAL_MILLISECONDS",
    "SENTRY_DSN",
    "SENTRY_ENVIRONMENT",
    "SENTRY_RATE_LIMIT_SECONDS",
    "SENTRY_RELEASE",
    "SENTRY_SAMPLE_RATE",
    "SENTRY_TAG_CLIENT_ID",
    "SENTRY_TAG_REQUEST_ID",
    "SENTRY_TAG_SESSION_ID",
    "SPAN_GENERATION",
    "SPAN_REQUEST",
    "SPAN_SESSION",
]
