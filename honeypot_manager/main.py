"""
Entry-point for Project H.I.V.E Honeypot-Manager API.
"""
from fastapi import FastAPI

from honeypot_manager.controllers.honeypot_manager_controller import router as hp_router
# NOTE: logging is initialised centrally in common.helpers
from common.helpers import logger  # noqa: F401 (imported for side‑effect only)

app = FastAPI(
    title="Project H.I.V.E - Honeypot-Manager API",
    description=(
        "REST endpoints that orchestrate honeypot containers inside rootless "
        "Podman - powered via CLI."
    ),
    version="2.0.0",
)

# Mount the honeypot-manager router at the root of the API
app.include_router(hp_router)

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",          # module:app reference
        host="localhost",      # bind to all interfaces
        port=8080,             # API port
        log_level="info",
    )