from __future__ import annotations
"""REST endpoints for Project-H.I.V.E log-manager."""

from typing import Dict, List
import subprocess

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from asyncio import TimeoutError

from log_manager.controllers.orchestrator import ServiceOrchestrator
from common.helpers import PodmanError, ResourceError, logger

router = APIRouter()

# ────────────────────────────── models ───────────────────────────────────────
class AdminPasswordBody(BaseModel):
    admin_password: str = Field(..., min_length=8,
                                description="Password for the OpenSearch admin user")

class SimpleResponse(BaseModel):
    message: str

class StatusResponse(BaseModel):
    open_search_node: str
    nats_server: str
    log_collector: str
    open_search_dashboard: str

# ───────────────────────────── helpers ───────────────────────────────────────
def _orchestrator(password: str | None = None) -> ServiceOrchestrator:
    return ServiceOrchestrator(password)

def _err(detail: str, code: int = status.HTTP_400_BAD_REQUEST):
    raise HTTPException(status_code=code, detail=detail)

def _dashboard_status() -> str:
    try:
        out = subprocess.check_output([
            "podman", "inspect", "-f", "{{.State.Status}}", "hive-opensearch-dash"
        ], text=True)
        return out.strip()
    except subprocess.CalledProcessError:
        return "not found"

# ───────────────────────────── endpoints ─────────────────────────────────────
@router.post("/create", response_model=SimpleResponse)
async def create_services(body: AdminPasswordBody):
    orch = _orchestrator(body.admin_password)
    if orch.any_exists():
        _err("Required containers already exist. Delete them before creating again.")
    try:
        await run_in_threadpool(orch.create_all)
        return {"message": "Containers created successfully"}
    except (PodmanError, ResourceError) as e:
        logger.exception("Create failed")
        _err(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/start", response_model=SimpleResponse)
async def start_services():
    orch = _orchestrator()
    miss = orch.missing()
    if miss:
        _err(f"Containers not found: {', '.join(miss)}. Create them first.")
    if not orch.not_running():
        return {"message": "Containers already running"}
    try:
        await run_in_threadpool(orch.start_all)
        return {"message": "Containers started successfully"}
    except TimeoutError as e:
        _err(str(e), status.HTTP_504_GATEWAY_TIMEOUT)
    except (PodmanError, ResourceError) as e:
        logger.exception("Start failed")
        _err(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/stop", response_model=SimpleResponse)
async def stop_services():
    orch = _orchestrator()
    if orch.missing():
        _err("Containers do not exist – nothing to stop.")
    if not orch.any_running():
        return {"message": "Containers already stopped"}
    try:
        await run_in_threadpool(orch.stop_all)
        return {"message": "Containers stopped successfully"}
    except (PodmanError, ResourceError) as e:
        logger.exception("Stop failed")
        _err(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.delete("/delete", response_model=SimpleResponse)
async def delete_services():
    orch = _orchestrator()
    if orch.missing():
        _err("Containers do not exist – nothing to delete.")
    if orch.any_running():
        _err("Containers are running. Stop them before deletion.")
    try:
        await run_in_threadpool(orch.delete_all)
        return {"message": "Containers deleted successfully"}
    except (PodmanError, ResourceError) as e:
        logger.exception("Delete failed")
        _err(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/status", response_model=StatusResponse)
async def status_services():
    orch = _orchestrator()
    s: Dict[str, str] = orch.status_report()
    return {
        "open_search_node": s.get("hive-opensearch-node", "not found"),
        "nats_server":      s.get("hive-nats-server",    "not found"),
        "log_collector":    s.get("hive-log-collector",  "not found"),
        "open_search_dashboard": _dashboard_status(),
    }

@router.get("/services", response_model=List[str])
async def list_running_services():
    orch = _orchestrator()
    running_map = orch._running_map()
    running = [name for name, is_run in running_map.items() if is_run]
    if _dashboard_status() == "running":
        running.append("hive-opensearch-dash")
    return running
