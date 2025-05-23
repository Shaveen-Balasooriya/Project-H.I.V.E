"""Domain‑specific exceptions for **Project H.I.V.E – Honeypot‑Manager**.

Every error inherits from :class:`HoneypotError`, provides a meaningful
``msg`` attribute, *and* is listed in ``__all__`` for clean re‑exports.
The controller layer can surface ``exc.msg`` directly in HTTP responses.
"""
from __future__ import annotations

__all__ = [
    "HoneypotError",
    "HoneypotExistsError",
    "HoneypotTypeNotFoundError",
    "HoneypotImageError",
    "HoneypotContainerError",
    "HoneypotPrivilegedPortError",
    "HoneypotActiveConnectionsError",
    "HoneypotPortInUseError",
]

###############################################################################
# Base class
###############################################################################

class HoneypotError(Exception):
    """Root of the honeypot‑error hierarchy."""

    def __init__(self, msg: str | None = None):
        super().__init__(msg or self.__class__.__name__)
        self.msg: str = msg or self.__class__.__name__

###############################################################################
# Creation / configuration errors
###############################################################################

class HoneypotExistsError(HoneypotError):
    """A container with the same name already exists."""


class HoneypotTypeNotFoundError(HoneypotError):
    """Requested honeypot *type* does not exist in config file."""


class HoneypotImageError(HoneypotError):
    """Failure while building or pulling the honeypot image."""


class HoneypotPortInUseError(HoneypotError):
    """Port is already in use by another honeypot or service."""

###############################################################################
# Runtime / lifecycle errors
###############################################################################

class HoneypotContainerError(HoneypotError):
    """Generic container operation failure (start/stop/restart/delete)."""


class HoneypotPrivilegedPortError(HoneypotError):
    """Rootless Podman cannot bind to privileged ports (<1024)."""


class HoneypotActiveConnectionsError(HoneypotError):
    """Stop/Delete refused: **established inbound connections** on host‑port."""
