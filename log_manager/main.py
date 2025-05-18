from __future__ import annotations

"""Entry-point for Project H.I.V.E – Log-Manager API."""

from fastapi import FastAPI
from log_manager.controllers.log_manager_router import router as log_router

app = FastAPI(
    title="Project H.I.V.E – Log-Manager API",
    description="REST endpoints that orchestrate OpenSearch, NATS and log-collector services inside rootless Podman.",
    version="2.0.0",
)

# include all endpoints at root
app.include_router(log_router)

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9090,
        reload=True,
        log_level="info",
    )