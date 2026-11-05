"""TensorRT-LLM server composition root."""

from __future__ import annotations

from src.telemetry.cuda import GPU_PROVIDER
from src.runtime.settings import read_settings
from src.server.readiness import ReadinessState
from src.engines.trt.factory import create_trt_engine
from config.model.quantization import TRT_ENGINE

from .listeners import run_applications
from .applications import create_public_application, create_readiness_application

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
readiness_application = create_readiness_application(readiness_state)


def main() -> None:
    """Run the TensorRT public and probe listeners."""
    run_applications(public_application, readiness_application, readiness_state, settings=settings)


if __name__ == "__main__":
    main()
