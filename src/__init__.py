"""Text Inference Server Package.

This package provides a high-performance inference server for text generation,
supporting both vLLM and TensorRT-LLM backends. The server handles:

- WebSocket-based real-time interactions
- Session management with conversation history
- Model quantization (AWQ, GPTQ, FP8)
- Prefix caching for improved latency

Architecture Overview:
    - ../config/: Root production and shared configuration modules
    - server/: Public WebSocket, loopback probe, and engine composition roots
    - engines/: Inference engine abstractions (vLLM, TRT-LLM)
    - execution/: Request execution pipeline
    - websocket/: WebSocket lifecycle and transport
    - session/: Session management
    - messages/: Message type handlers (start, message, cancel)
    - tokens/: Tokenization utilities
    - files/, logging/: Runtime support modules

Example:
    Start the selected dual-listener server process:

    $ INFERENCE_ENGINE=vllm python -m src.server.vllm
    $ INFERENCE_ENGINE=trt python -m src.server.trt

Environment Variables:
    Required:
        - MAX_CONCURRENT_CONNECTIONS: Maximum WebSocket connections
        - API_KEY: API key for authentication
        - MODEL: HuggingFace model ID or local path

    Optional:
        - RUNTIME_QUANTIZATION: Detected runtime checkpoint format
        - INFERENCE_ENGINE: 'vllm' or 'trt' (default: 'trt')

"""

from src.logging.output import configure_dependency_output

configure_dependency_output()
