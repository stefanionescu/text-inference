# Multi-stage build for efficient Docker image
# CUDA 13.0 with Ubuntu 24.04 for vLLM 0.25.1
FROM nvidia/cuda:13.0.0-cudnn-devel-ubuntu24.04 AS builder
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /usr/local/bin/

ENV FLASHINFER_VERSION=0.6.13

ARG APT_PYTHON312_VERSION=3.12.3-1ubuntu0.13
ARG APT_CA_CERTIFICATES_VERSION=20240203
ARG APT_GIT_VERSION=1:2.43.0-1ubuntu7.3
ARG APT_WGET_VERSION=1.21.4-1ubuntu4.1
ARG APT_CURL_VERSION=8.5.0-2ubuntu10.9
ARG APT_GCC_VERSION=4:13.2.0-7ubuntu1
ARG APT_GXX_VERSION=4:13.2.0-7ubuntu1
ARG APT_MAKE_VERSION=4.3-4.1build2
ARG APT_CMAKE_VERSION=3.28.3-1build7
ARG APT_NINJA_BUILD_VERSION=1.11.1-2

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV VENV_DIR=/opt/venv
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0;10.0;10.3;12.0"
ENV FORCE_CUDA=1
ENV MAX_JOBS=8

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12=${APT_PYTHON312_VERSION} \
    python3.12-dev=${APT_PYTHON312_VERSION} \
    python3.12-venv=${APT_PYTHON312_VERSION} \
    ca-certificates=${APT_CA_CERTIFICATES_VERSION} \
    git=${APT_GIT_VERSION} \
    wget=${APT_WGET_VERSION} \
    curl=${APT_CURL_VERSION} \
    gcc=${APT_GCC_VERSION} \
    g++=${APT_GXX_VERSION} \
    make=${APT_MAKE_VERSION} \
    cmake=${APT_CMAKE_VERSION} \
    ninja-build=${APT_NINJA_BUILD_VERSION} \
    && rm -rf /var/lib/apt/lists/*

# Create Python virtual environment
RUN python3.12 -m venv "${VENV_DIR}"
ENV PATH="${VENV_DIR}/bin:${PATH}"

# Copy locked dependency inputs and install Python dependencies
WORKDIR /app
COPY pyproject.toml uv.lock /app/
COPY src/__init__.py /app/src/
RUN set -eux; \
    export UV_NO_PROGRESS=1 UV_PYTHON_DOWNLOADS=never FLASHINFER_ENABLE_AOT=1; \
    UV_PROJECT_ENVIRONMENT="${VENV_DIR}" uv sync --frozen --no-dev --extra vllm --no-install-project --python "${VENV_DIR}/bin/python" --no-python-downloads --no-install-package flashinfer-python --no-install-package flashinfer-cubin; \
    uv pip install --python "${VENV_DIR}/bin/python" --prefer-binary --extra-index-url "https://flashinfer.ai/whl/cu130/torch2.11" "flashinfer-python==${FLASHINFER_VERSION}" "flashinfer-cubin==${FLASHINFER_VERSION}"

# =============================================================================
# Production stage
# =============================================================================
FROM nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04

# Model configuration - set and downloaded at build time
ARG MODEL
ARG MODEL_REVISION
ARG APT_PYTHON312_VERSION=3.12.3-1ubuntu0.13
ARG APT_CA_CERTIFICATES_VERSION=20240203
ARG APT_CURL_VERSION=8.5.0-2ubuntu10.9
ARG APT_GNUPG_VERSION=2.4.4-2ubuntu17.4
ARG APT_OPENSSL_VERSION=3.0.13-0ubuntu3.11

# Set environment variables for production
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV VENV_DIR=/opt/venv
ENV PATH="${VENV_DIR}/bin:${PATH}"

# Configured models - these are set at build time
ENV MODEL=${MODEL}
ENV MODEL_REVISION=${MODEL_REVISION}

# Engine type for vLLM
ENV INFERENCE_ENGINE=vllm

# Default directories for baked-in models
ENV MODELS_DIR=/opt/models
ENV MODEL_PATH=/opt/models/model

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade \
    dirmngr=${APT_GNUPG_VERSION} \
    gnupg=${APT_GNUPG_VERSION} \
    gnupg-utils=${APT_GNUPG_VERSION} \
    gnupg2=${APT_GNUPG_VERSION} \
    gpg=${APT_GNUPG_VERSION} \
    gpg-agent=${APT_GNUPG_VERSION} \
    gpgconf=${APT_GNUPG_VERSION} \
    gpgsm=${APT_GNUPG_VERSION} \
    gpgv=${APT_GNUPG_VERSION} \
    keyboxd=${APT_GNUPG_VERSION} \
    libssl3t64=${APT_OPENSSL_VERSION} \
    openssl=${APT_OPENSSL_VERSION} \
    && apt-get install -y --no-install-recommends \
    python3.12=${APT_PYTHON312_VERSION} \
    python3.12-venv=${APT_PYTHON312_VERSION} \
    ca-certificates=${APT_CA_CERTIFICATES_VERSION} \
    curl=${APT_CURL_VERSION} \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create app directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/.run /app/.hf /app/.vllm_cache /opt/models/model

# Cache directories
ENV HF_HOME=/app/.hf
ENV HUGGINGFACE_HUB_CACHE=/app/.hf/hub
ENV VLLM_CACHE_DIR=/app/.vllm_cache
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    GIT_SSL_CAINFO=/etc/ssl/certs/ca-certificates.crt

COPY docker/shared/download/snapshot.py /app/docker/shared/download/snapshot.py

RUN --mount=type=secret,id=hf_token,required=false \
    "${VENV_DIR}/bin/python" /app/docker/shared/download/snapshot.py

ENV MODEL=/opt/models/model

COPY src/ /app/src/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY shared/scripts/ /app/shared/scripts/
RUN RUNTIME_QUANTIZATION="$("${VENV_DIR}/bin/python" -m src.quantization.detection /opt/models/model)" \
    "${VENV_DIR}/bin/python" -m src.scripts.validate \
    && rm -rf /app/docker

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && touch /app/server.log \
    && chown -R appuser:appuser /app /opt/models /opt/venv

ENV LOGS_ENABLED=0 \
    DEPENDENCY_LOG_FILE=-

USER 10001

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["/app/scripts/probe.sh"]

# Default command
CMD ["/app/scripts/main.sh"]

LABEL org.opencontainers.image.title="Text Inference vLLM (CUDA 13.0, Py312)" \
      org.opencontainers.image.description="vLLM 0.25.1 inference image with FlashInfer 0.6.13."
