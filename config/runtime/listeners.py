"""Fixed public and loopback listener configuration."""

PUBLIC_SERVER_HOST_OCTETS = ("0", "0", "0", "0")
PUBLIC_SERVER_PORT = 8000
PROBE_SERVER_HOST = "127.0.0.1"
PROBE_SERVER_PORT = 8001

__all__ = [
    "PROBE_SERVER_HOST",
    "PROBE_SERVER_PORT",
    "PUBLIC_SERVER_HOST_OCTETS",
    "PUBLIC_SERVER_PORT",
]
