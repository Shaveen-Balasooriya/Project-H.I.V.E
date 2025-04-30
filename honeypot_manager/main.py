from __future__ import annotations

"""Entry‑point for Project H.I.V.E Honeypot‑Manager API.

This file mirrors the structure of *log_manager/main.py* so both services are
uniform.  No ad‑hoc logging configuration is performed here – we inherit the
root configuration defined in ``common.helpers``.
"""

from fastapi import FastAPI

from honeypot_manager.controllers.honeypot_manager_controller import router as hp_router

# NOTE: logging is initialised centrally in ``common.helpers`` – just import it
from common.helpers import logger  # noqa: F401  # imported for side‑effect only

###############################################################################
# FastAPI application
###############################################################################
app = FastAPI(
    title="Project H.I.V.E – Honeypot‑Manager API",
    description=(
        "REST endpoints that orchestrate honeypot containers inside rootless "
        "Podman – powered via CLI (no SDK)."
    ),
    version="2.0.0",
)

# Mount router under */honeypot_manager* namespace (parity with log‑manager)
app.include_router(hp_router, prefix="/honeypot_manager", tags=["honeypot_manager"])

###############################################################################
# Uvicorn convenience – identical pattern to Log‑Manager
###############################################################################
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",  # module:object reference
        host="0.0.0.0",
        port=8081,  # distinct port so both APIs can run side‑by‑side
        reload=True,
        log_level="info",
    )
