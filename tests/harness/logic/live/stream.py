"""Live response stream helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import field, dataclass

from tests.harness.client.websocket import record_token
from tests.harness.reporting.terminal import magenta, write_line, write_text

if TYPE_CHECKING:
    from tests.state.metrics import StreamState


@dataclass
class _StreamPrinter:
    """Print streaming tokens to standard output."""

    is_header_printed: bool = False

    def write_chunk(self, chunk: str) -> None:
        if not chunk:
            return
        if not self.is_header_printed:
            write_text(f"\n{magenta('ASST')} ", is_flush_requested=True)
            self.is_header_printed = True
        write_text(chunk, is_flush_requested=True)

    def finish(self) -> None:
        if not self.is_header_printed:
            return
        write_line()
        write_line()


@dataclass
class _StreamContext:
    """Track state during response streaming."""

    state: StreamState
    printer: _StreamPrinter = field(default_factory=_StreamPrinter)
    pending_ttfb_milliseconds: float | None = None

    def handle_token(self, chunk: str) -> None:
        metrics = record_token(self.state, chunk)
        self.printer.write_chunk(chunk)
        ttfb = metrics.get("ttfb_ms")
        if ttfb is not None and self.pending_ttfb_milliseconds is None:
            self.pending_ttfb_milliseconds = ttfb


__all__ = ["_StreamContext"]
