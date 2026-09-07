"""vLLM ASGI application."""

from .listeners import run_applications
from src.telemetry.cuda import GPU_PROVIDER
from src.runtime.settings import read_settings
from src.server.readiness import ReadinessState
from config.model.quantization import VLLM_ENGINE
from src.engines.vllm.factory import create_vllm_engine
from .applications import create_probe_application, create_public_application

settings = read_settings()
if settings.engine.inference_engine != VLLM_ENGINE:
    message = "vLLM server requires INFERENCE_ENGINE=vllm"
    raise RuntimeError(message)

readiness_state = ReadinessState()
public_application = create_public_application(
    settings,
    create_vllm_engine,
    gpu_provider=GPU_PROVIDER,
    readiness_state=readiness_state,
)
probe_application = create_probe_application(readiness_state)


def main() -> None:
    """Run the vLLM public and probe listeners."""
    run_applications(
        public_application,
        probe_application,
        readiness_state,
        is_logging_enabled=settings.engine.is_logging_enabled,
    )


if __name__ == "__main__":
    main()


__all__ = ["main", "probe_application", "public_application"]
