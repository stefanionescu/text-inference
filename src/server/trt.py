"""TensorRT-LLM server composition root."""

from __future__ import annotations

from .listeners import run_applications
from src.telemetry.cuda import GPU_PROVIDER
from src.runtime.settings import read_settings
from src.server.readiness import ReadinessState
from config.model.quantization import TRT_ENGINE
from src.engines.trt.factory import create_trt_engine
from .applications import create_probe_application, create_public_application

settings = read_settings()
if settings.engine.inference_engine != TRT_ENGINE:
    message = "TensorRT server requires INFERENCE_ENGINE=trt"
    raise RuntimeError(message)

readiness_state = ReadinessState()
public_application = create_public_application(
    settings,
    create_trt_engine,
    gpu_provider=GPU_PROVIDER,
    readiness_state=readiness_state,
)
probe_application = create_probe_application(readiness_state)


def main() -> None:
    """Run the TensorRT public and probe listeners."""
    run_applications(
        public_application,
        probe_application,
        readiness_state,
        is_logging_enabled=settings.engine.is_logging_enabled,
    )


if __name__ == "__main__":
    main()


__all__ = ["main", "probe_application", "public_application"]
