# TensorRT-LLM production image for pre-quantized models
# CUDA 13.1 with Ubuntu 24.04 (TRT-LLM 1.3.0rc20 uses torch 2.10.0+cu130)
#
FROM nvidia/cuda:13.1.2-cudnn-devel-ubuntu24.04 AS builder
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /usr/local/bin/

# Use bash for RUN lines
SHELL ["/bin/bash", "-lc"]

# Non-interactive APT
ENV DEBIAN_FRONTEND=noninteractive

# Build-time runtime pins
ARG APT_CA_CERTIFICATES_VERSION=20240203
ARG APT_CURL_VERSION=8.5.0-2ubuntu10.9
ARG APT_GIT_VERSION=1:2.43.0-1ubuntu7.3
ARG APT_WGET_VERSION=1.21.4-1ubuntu4.1
ARG APT_JQ_VERSION=1.7.1-3ubuntu0.24.04.2
ARG APT_PYTHON312_VERSION=3.12.3-1ubuntu0.13
ARG APT_BUILD_ESSENTIAL_VERSION=12.10ubuntu1
ARG APT_LIBZMQ3_DEV_VERSION=4.3.5-1build2
ARG MPI_VERSION_PIN=4.1.6-7ubuntu2

ENV VENV_FOLDER=/opt/venv

# ----------------------------------------------------------------------------
# Builder bootstrap
# ----------------------------------------------------------------------------
# NOTE: Ubuntu 24.04 uses libopenmpi3t64 (t64 transition packages).
# We pin MPI versions and use --no-upgrade to prevent CUDA downgrades.
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      ca-certificates=${APT_CA_CERTIFICATES_VERSION} \
      curl=${APT_CURL_VERSION} \
      git=${APT_GIT_VERSION} \
      wget=${APT_WGET_VERSION} \
      jq=${APT_JQ_VERSION} && \
    apt-get install -y --no-install-recommends --no-upgrade \
      python3.12=${APT_PYTHON312_VERSION} \
      python3.12-venv=${APT_PYTHON312_VERSION} \
      python3.12-dev=${APT_PYTHON312_VERSION} \
      libopenmpi3t64=${MPI_VERSION_PIN} \
      openmpi-bin=${MPI_VERSION_PIN} \
      openmpi-common=${MPI_VERSION_PIN} \
      build-essential=${APT_BUILD_ESSENTIAL_VERSION} \
      libzmq3-dev=${APT_LIBZMQ3_DEV_VERSION} && \
    apt-mark hold libopenmpi3t64 openmpi-bin openmpi-common && \
    rm -rf /var/lib/apt/lists/*

# Create virtual env
RUN python3.12 -m venv "${VENV_FOLDER}"

# Make venv default
ENV PATH="${VENV_FOLDER}/bin:${PATH}"

# ----------------------------------------------------------------------------
# App Python dependencies
# ----------------------------------------------------------------------------
WORKDIR /app
COPY pyproject.toml uv.lock /app/
RUN UV_PROJECT_ENVIRONMENT="${VENV_FOLDER}" \
    uv sync --frozen --no-dev --extra trt --no-install-project --python "${VENV_FOLDER}/bin/python" --no-python-downloads

# Prefer system CUDA libraries.
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# =============================================================================
# Production stage
# =============================================================================
FROM nvidia/cuda:13.1.2-cudnn-runtime-ubuntu24.04

# Use bash for RUN lines
SHELL ["/bin/bash", "-lc"]

# Non-interactive APT
ENV DEBIAN_FRONTEND=noninteractive

# Model configuration set and downloaded at build time
ARG MODEL
ARG MODEL_REVISION

# Runtime package pins
ARG APT_CA_CERTIFICATES_VERSION=20240203
ARG APT_CURL_VERSION=8.5.0-2ubuntu10.9
ARG APT_GNUPG_VERSION=2.4.4-2ubuntu17.4
ARG APT_LIBZMQ5_VERSION=4.3.5-1build2
ARG APT_OPENSSL_VERSION=3.0.13-0ubuntu3.11
ARG APT_PYTHON312_VERSION=3.12.3-1ubuntu0.13
ARG MPI_VERSION_PIN=4.1.6-7ubuntu2

ENV VENV_FOLDER=/opt/venv
ENV PATH="${VENV_FOLDER}/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# ----------------------------------------------------------------------------
# Runtime bootstrap
# ----------------------------------------------------------------------------
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      ca-certificates=${APT_CA_CERTIFICATES_VERSION} \
      curl=${APT_CURL_VERSION} \
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
      openssl=${APT_OPENSSL_VERSION} && \
    apt-get install -y --no-install-recommends --no-upgrade \
      python3.12=${APT_PYTHON312_VERSION} \
      libopenmpi3t64=${MPI_VERSION_PIN} \
      openmpi-bin=${MPI_VERSION_PIN} \
      openmpi-common=${MPI_VERSION_PIN} \
      libzmq5=${APT_LIBZMQ5_VERSION} && \
    apt-mark hold libopenmpi3t64 openmpi-bin openmpi-common && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# ----------------------------------------------------------------------------
# Production environment setup
# ----------------------------------------------------------------------------
# Configure models - these are set at build time and used at runtime
ENV MODEL=${MODEL}
ENV MODEL_REVISION=${MODEL_REVISION}

# Engine type
ENV INFERENCE_ENGINE=trt

# Default directory for the baked checkpoint
ENV MODELS_DIR=/opt/models
ENV MODEL_PATH=/opt/models/model
RUN mkdir -p "${MODELS_DIR}" "${MODEL_PATH}"

# Cache directories
ENV HF_HOME=/app/.hf
ENV HUGGINGFACE_HUB_CACHE=/app/.hf/hub
RUN mkdir -p /app/logs /app/.run /app/.hf

COPY docker/base/download/snapshot.py /app/docker/base/download/snapshot.py

RUN --mount=type=secret,id=hf_token,required=false \
    "${VENV_FOLDER}/bin/python" /app/docker/base/download/snapshot.py

ENV MODEL=/opt/models/model

COPY src/ /app/src/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY base/scripts/ /app/base/scripts/
RUN RUNTIME_QUANTIZATION="$("${VENV_FOLDER}/bin/python" -m src.quantization.detection /opt/models/model)" \
    "${VENV_FOLDER}/bin/python" -m src.scripts.validate \
    && rm -rf /app/docker

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && touch /app/server.log \
    && chown -R appuser:appuser /app /opt/models /opt/venv

# Default environment knobs for production
ENV HF_HUB_ENABLE_HF_TRANSFER=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1

ENV LOGS_ENABLED=0 \
    DEPENDENCY_LOG_FILE=-

# SSL certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    GIT_SSL_CAINFO=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

USER 10001

# Health check for production readiness
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD ["/app/scripts/readiness.sh"]

EXPOSE 8000

# Default command: start the server
CMD ["/app/scripts/main.sh"]

LABEL org.opencontainers.image.title="Text Inference TRT-LLM (CUDA 13.1, Py312)" \
      org.opencontainers.image.description="TensorRT-LLM public PyTorch backend inference image."
