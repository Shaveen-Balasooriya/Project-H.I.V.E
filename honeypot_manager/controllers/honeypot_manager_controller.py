"""Controller for Project H.I.V.E Honeypot-Manager API.

Delegates all orchestration logic to the HoneypotManager model.
Defines routes, schemas, and HTTP error mapping only.
"""
from typing import Any, Dict, List
import json
import yaml
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Path as PathParam

from common.helpers import PodmanRunner, PodmanError, ResourceError, logger
from honeypot_manager.models.Honeypot import HoneypotManager, HoneypotConfig
from honeypot_manager.schemas.honeypot_schemas import (
    HoneypotCreate,
    HoneypotResponse,
    PortCheckResponse,
)
from honeypot_manager.util.exceptions import (
    HoneypotExistsError,
    HoneypotImageError,
    HoneypotContainerError,
    HoneypotPrivilegedPortError,
    HoneypotActiveConnectionsError,
    HoneypotTypeNotFoundError,
    HoneypotPortInUseError,
    HoneypotError,
)

router = APIRouter(prefix="", tags=["honeypot-manager"])

# ──────────────────────────────────────────────────────────────────────────────
# Error mapping helper
# ──────────────────────────────────────────────────────────────────────────────
_ERROR_MAP: Dict[type, tuple[str, int]] = {
    HoneypotExistsError:        ("Honeypot already exists",                status.HTTP_409_CONFLICT),
    HoneypotImageError:         ("Failed to build/pull honeypot image",     status.HTTP_500_INTERNAL_SERVER_ERROR),
    HoneypotContainerError:     ("Container operation failed",              status.HTTP_500_INTERNAL_SERVER_ERROR),
    HoneypotPrivilegedPortError:("Privileged port requires elevated access",status.HTTP_400_BAD_REQUEST),
    HoneypotActiveConnectionsError:("Active connections block this action",   status.HTTP_423_LOCKED),
    HoneypotTypeNotFoundError:  ("Unknown honeypot type",                   status.HTTP_404_NOT_FOUND),
    HoneypotPortInUseError:     ("Port already in use",                      status.HTTP_409_CONFLICT),
    HoneypotError:              ("Honeypot operation error",                status.HTTP_500_INTERNAL_SERVER_ERROR),
    PodmanError:                ("Podman runtime error",                    status.HTTP_500_INTERNAL_SERVER_ERROR),
    ResourceError:              ("Host resource error",                     status.HTTP_500_INTERNAL_SERVER_ERROR),
    ValueError:                 ("Invalid parameter",                       status.HTTP_400_BAD_REQUEST),
    FileNotFoundError:          ("Configuration not found",                 status.HTTP_404_NOT_FOUND),
    PermissionError:            ("Permission denied",                       status.HTTP_403_FORBIDDEN),
}


def _err(exc: Exception) -> None:
    """Convert internal exceptions to HTTPExceptions with proper status/detail."""
    if isinstance(exc, HTTPException):
        raise exc
    base_msg, code = _ERROR_MAP.get(type(exc), (str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR))
    detail = str(exc) if str(exc) != type(exc).__name__ else base_msg
    raise HTTPException(status_code=code, detail=detail)

# ──────────────────────────────────────────────────────────────────────────────
# Podman helpers
# ──────────────────────────────────────────────────────────────────────────────
_runner = PodmanRunner()

def _list_container_ids(*filters: str) -> List[str]:
    cmd = ["podman", "ps", "-a", "--format", "json"] + [f"--filter={f}" for f in filters]
    out = _runner.run(cmd, return_output=True) or "[]"
    return [c["Id"] for c in json.loads(out)]


def _pack_responses(ids: List[str]) -> List[HoneypotResponse]:
    """Convert Podman container IDs into API response objects."""
    result: List[HoneypotResponse] = []
    for cid in ids:
        hp = HoneypotManager()
        if hp.get_honeypot_details(cid):
            result.append(HoneypotResponse(**hp.to_dict()))
    return result

# ──────────────────────────────────────────────────────────────────────────────
# CRUD Endpoints
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[HoneypotResponse])
async def list_all() -> List[HoneypotResponse]:
    """List all honeypot containers."""
    try:
        ids = _list_container_ids("label=service=hive-honeypot-manager")
        return _pack_responses(ids)
    except Exception as exc:
        _err(exc)

@router.get("/name/{name}", response_model=HoneypotResponse)
async def inspect(name: str) -> HoneypotResponse:
    """Inspect a single honeypot by container name."""
    try:
        hp = HoneypotManager()
        if not hp.get_honeypot_details(name):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Honeypot not found")
        return HoneypotResponse(**hp.to_dict())
    except Exception as exc:
        _err(exc)

@router.post("/", response_model=HoneypotResponse, status_code=status.HTTP_201_CREATED)
async def create(body: HoneypotCreate) -> HoneypotResponse:
    """Create a new honeypot container with the provided settings."""
    try:
        hp = HoneypotManager()
        data = body.model_dump()
        hp.create_honeypot(**data)
        return HoneypotResponse(**hp.to_dict())
    except Exception as exc:
        _err(exc)

# ──────────────────────────────────────────────────────────────────────────────
# Lifecycle Endpoints
# ──────────────────────────────────────────────────────────────────────────────
def _lifecycle_action(name: str, action: str, msg: str) -> Dict[str, Any]:
    hp = HoneypotManager()
    if not hp.get_honeypot_details(name):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Honeypot '{name}' not found")
    try:
        getattr(hp, f"{action}_honeypot")()
        if action != "delete":
            hp.get_honeypot_details(hp.honeypot_name)
        return {"message": msg, "honeypot": hp.to_dict()}
    except Exception as exc:
        _err(exc)

@router.post("/{name}/start")
async def start(name: str) -> Dict[str, Any]:
    """Start a stopped honeypot."""
    return _lifecycle_action(name, "start",   "Honeypot started successfully")

@router.post("/{name}/stop")
async def stop(name: str) -> Dict[str, Any]:
    """Stop a running honeypot."""
    return _lifecycle_action(name, "stop",    "Honeypot stopped successfully")

@router.post("/{name}/restart")
async def restart(name: str) -> Dict[str, Any]:
    """Restart an existing honeypot."""
    return _lifecycle_action(name, "restart", "Honeypot restarted successfully")

@router.delete("/{name}")
async def delete(name: str) -> Dict[str, Any]:
    """Delete a honeypot (must be stopped first)."""
    return _lifecycle_action(name, "delete",  "Honeypot deleted successfully")

# ──────────────────────────────────────────────────────────────────────────────
# Metadata & Filters
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/types", response_model=List[str])
async def list_types() -> List[str]:
    """List all supported honeypot types."""
    return HoneypotConfig.types()

@router.get("/types/{t}/config")
async def get_type_config(t: str) -> Dict[str, Any]:
    """Get default configuration for honeypot type `t`."""
    try:
        return HoneypotConfig.get(t)
    except Exception as exc:
        _err(exc)

@router.get("/types/{t}/auth-details")
async def get_auth_details(t: str) -> Dict[str, Any]:
    cfg_path = (
        Path(__file__).resolve().parent.parent
        / "honeypots"
        / t
        / "config.yaml"
    )
    if not cfg_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No auth/banner found")
    cfg = yaml.safe_load(cfg_path.read_text()) or {}

    data: Dict[str, Any] = {}
    if "authentication" in cfg:
        data["authentication"] = cfg["authentication"]
    if "banner" in cfg:
        data["banner"] = cfg["banner"]
    if not data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No auth/banner found")
    return data

@router.get("/type/{t}", response_model=List[HoneypotResponse])
async def list_by_type(t: str) -> List[HoneypotResponse]:
    """List honeypots filtered by type `t`."""
    try:
        if t not in HoneypotConfig.types():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unknown type")
        ids = _list_container_ids("label=service=hive-honeypot-manager", f"label=hive.type={t}")
        hps = _pack_responses(ids)
        if not hps:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No honeypots of this type")
        return hps
    except Exception as exc:
        _err(exc)

@router.get("/status/{st}", response_model=List[HoneypotResponse])
async def list_by_status(st: str) -> List[HoneypotResponse]:
    """List honeypots by status (`created`, `started`, `exited`)."""
    valid = {"created","started","exited"}
    if st not in valid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Status must be one of: {valid}")
    try:
        ids = _list_container_ids("label=service=hive-honeypot-manager")
        hps = _pack_responses(ids)
        filtered = [hp for hp in hps if (st=="started" and hp.status=="running") or hp.status==st]
        if not filtered:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No honeypots with that status")
        return filtered
    except Exception as exc:
        _err(exc)

@router.get(
    "/port-check/{port}",
    response_model=PortCheckResponse,
    summary="Check if a port is available",
    description="Validate that `port` is free and within range for a new honeypot."
)
async def check_port(port: int = PathParam(..., description="Port to test")) -> PortCheckResponse:
    """Port availability check using HoneypotManager.is_port_in_use()."""
    if not (1 <= port <= 65_535):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Port out of valid range")
    if port < 1024:
        return PortCheckResponse(available=False, message="Root required for privileged ports")
    try:
        in_use = HoneypotManager().is_port_in_use(port)
        return PortCheckResponse(
            available=not in_use,
            message=f"Port {port} {'in use' if in_use else 'available'}"
        )
    except Exception as exc:
        logger.error("Port-check error: %s", exc)
        _err(exc)