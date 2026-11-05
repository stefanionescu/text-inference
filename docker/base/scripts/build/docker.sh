#!/usr/bin/env bash
# Shared Docker helper functions for build scripts.
#
# Provides shared Docker operations used by both TRT and vLLM build scripts,
# including Docker availability checks and login handling.

# require_docker: Stop the build when the Docker command is not installed.
require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    log_write "[build] ✗ Docker CLI not found. Please install Docker and try again."
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    log_write "[build] ✗ Docker is not running. Please start Docker and try again."
    exit 1
  fi
}
