"""Uvicorn server behavior for the loopback probe listener."""

from __future__ import annotations

import uvicorn
import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator


class ProbeServer(uvicorn.Server):
    """Run without competing for process signal ownership."""

    def install_signal_handlers(self) -> None:
        """Leave signal ownership with the public server."""

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None, None, None]:
        """Leave signal ownership with the public server."""
        yield


__all__ = ["ProbeServer"]
