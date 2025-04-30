"""REST controller – updated with safety guards & structured responses."""
from __future__ import annotations

import json
import re
from typing import List, Dict, Any
import subprocess
import yaml
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from honeypot_manager.models.Honeypot import HoneypotManager as Honeypot
from honeypot_manager.models.Honeypot import HoneypotConfig
from honeypot_manager.schemas.honeypot import HoneypotCreate, HoneypotResponse
from honeypot_manager.util.exceptions import (
    HoneypotActiveConnectionsError,
    HoneypotContainerError,
    HoneypotExistsError,
    HoneypotImageError,
    HoneypotPrivilegedPortError,
    HoneypotTypeNotFoundError,
    HoneypotError,
)
from common.helpers import PodmanError, ResourceError, PodmanRunner, logger

router = APIRouter(prefix="/honeypot-manager", tags=["honeypot-manager"])

###############################################################################
# Error mapping – shared helper
###############################################################################
# Base error mappings
_ERROR_MAP: Dict[type, tuple[str, int]] = {
    HoneypotExistsError: ("Honeypot already exists with this name and port", status.HTTP_409_CONFLICT),
    HoneypotImageError: ("Failed to build / pull honeypot image", 500),
    HoneypotContainerError: ("Container operation failed", 500),  # Default fallback
    HoneypotPrivilegedPortError: (
        "Port <1024 needs CAP_NET_BIND_SERVICE or root privileges", 400
    ),
    HoneypotActiveConnectionsError: (
        "Active inbound connections detected – refuse operation", 423  # Locked
    ),
    HoneypotTypeNotFoundError: ("Unknown honeypot type", 404),
    HoneypotError: ("Honeypot operation error", 500),
    PodmanError: ("Podman runtime error", 500),
    ResourceError: ("Host resource error", 500),
    # Add built-in exception mappings below
    ValueError: ("Invalid parameter", status.HTTP_400_BAD_REQUEST),
    FileNotFoundError: ("Configuration not found", status.HTTP_404_NOT_FOUND),
    PermissionError: ("Permission denied", status.HTTP_403_FORBIDDEN),
    subprocess.CalledProcessError: ("System subprocess error", status.HTTP_500_INTERNAL_SERVER_ERROR),
}

# Common error patterns to simplify
_ERROR_PATTERNS = [
    # Pattern for "already in use" errors
    (
        r'creating container storage: the container name "([^"]+)" is already in use', 
        r'Honeypot \1 already exists'
    ),
    # Pattern for "already exists" from honeypot creation
    (
        r'Honeypot ([^ ]+) already exists by ([a-f0-9]+)',
        r'Honeypot \1 already exists. Please use a different port for this honeypot type.'
    ),
    # Pattern for permission errors
    (
        r'permission denied.*',
        'Permission denied - check container privileges'
    ),
    # Pattern for "no such container"
    (
        r'no such container.*"([^"]+)"',
        r'Honeypot \1 not found'
    ),
    # Pattern for "already running"
    (
        r'container ([^ ]+) is already running',
        r'Honeypot \1 is already running'
    ),
    # Pattern for "not running"
    (
        r'container ([^ ]+) is not running',
        r'Honeypot \1 is not running'
    )
]

def _simplify_error_message(message: str) -> str:
    """Simplify long Podman error messages to user-friendly form."""
    for pattern, replacement in _ERROR_PATTERNS:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    
    # Special handling for honeypot name already exists errors
    if "that name is already in use" in message or "already exists" in message:
        # Try to extract the honeypot name
        match = re.search(r'--name ([^ ]+)', message)
        if match:
            honeypot_name = match.group(1)
            honeypot_type = honeypot_name.split('-')[1] if len(honeypot_name.split('-')) > 2 else "unknown"
            honeypot_port = honeypot_name.split('-')[2] if len(honeypot_name.split('-')) > 2 else "unknown"
            return f"A honeypot of type '{honeypot_type}' with port {honeypot_port} already exists. Please use a different port."
        return "A honeypot with this name already exists. Please use a different port."
    
    # If no specific pattern matches, handle long error messages
    if len(message) > 100:
        # Find the most relevant part of the message
        if "Error:" in message:
            parts = message.split("Error:", 1)
            return "Error: " + parts[1].strip()
    
    return message

def _err(exc: Exception):  # noqa: D401 – small helper
    if isinstance(exc, HTTPException):
        raise exc
        
    # Use specific error message if available
    if hasattr(exc, 'msg') and exc.msg:
        message = exc.msg
    else:
        message = str(exc)
    
    # Special handling for HoneypotExistsError to create a more user-friendly error
    if isinstance(exc, HoneypotExistsError):
        honeypot_name = str(exc)
        parts = honeypot_name.split('-')
        if len(parts) >= 3:
            honeypot_type = parts[1]
            port = parts[2]
            message = f"A honeypot of type '{honeypot_type}' using port {port} already exists. Please use a different port."
        else:
            message = f"Honeypot '{honeypot_name}' already exists. Please use a different name or port."
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )
    
    # Simplify error message for other types
    message = _simplify_error_message(message)
        
    # Get default error code for this exception type
    error_type = type(exc)
    default_msg, code = _ERROR_MAP.get(error_type, (message, 500))
    
    # Use specific message if available, otherwise use default
    final_message = message if message != error_type.__name__ else default_msg
    
    raise HTTPException(status_code=code, detail=final_message)

###############################################################################
# helpers – discovery + response packing
###############################################################################
_runner = PodmanRunner()


def _list_ids(*flt: str) -> List[str]:
    cmd = ["podman", "ps", "-a", "--format", "json"]
    for f in flt:
        cmd += ["--filter", f]
    try:
        out = _runner.run(cmd, return_output=True) or "[]"
    except PodmanError as exc:
        _err(exc)
    ids = [e["Id"] for e in json.loads(out)]
    return ids


def _hp_responses(ids: List[str]) -> List[HoneypotResponse]:
    res: List[HoneypotResponse] = []
    for cid in ids:
        hp = Honeypot()
        if hp.get_honeypot_details(cid):
            res.append(HoneypotResponse(**hp.to_dict()))
    return res

###############################################################################
# list / inspect
###############################################################################
@router.get("/", response_model=List[HoneypotResponse])
async def list_all():
    try:
        return _hp_responses(_list_ids("label=service=hive-honeypot-manager"))
    except Exception as exc:
        _err(exc)


@router.get("/name/{name}", response_model=HoneypotResponse)
async def inspect(name: str):
    hp = Honeypot()
    if not hp.get_honeypot_details(name):
        _err(HTTPException(status_code=404, detail="Honeypot not found"))
    return HoneypotResponse(**hp.to_dict())

###############################################################################
# create
###############################################################################
@router.post("/", response_model=HoneypotResponse, status_code=201)
async def create(body: HoneypotCreate):
    hp = Honeypot()
    try:
        # Use model_dump() to convert the Pydantic model to a dict
        honeypot_data = body.model_dump()
        
        # Extract authentication and banner for config update
        authentication = honeypot_data.pop('authentication', None)
        banner = honeypot_data.pop('banner', None)
        
        # No need to convert authentication again as it's already a dict after model_dump()
        
        # Add authentication and banner back to the parameters for create_honeypot
        honeypot_data['authentication'] = authentication
        honeypot_data['banner'] = banner
        
        hp.create_honeypot(**honeypot_data)
        hp.get_honeypot_details(hp.honeypot_name)
        return HoneypotResponse(**hp.to_dict())
    except Exception as exc:
        _err(exc)

###############################################################################
# lifecycle – returns dict with message *and* honeypot details
###############################################################################

def _do(verb: str, name: str, msg: str):
    hp = Honeypot()
    # Get honeypot details returns None instead of raising when not found
    if not hp.get_honeypot_details(name):
        # Return a proper 404 response when honeypot doesn't exist
        _err(HTTPException(status_code=404, detail=f"Honeypot '{name}' not found"))

    if verb == "delete" and hp.honeypot_status == "running":
        _err(HoneypotContainerError("Cannot delete a running honeypot – stop it first"))

    op = getattr(hp, f"{verb}_honeypot")
    try:
        op()
        # For deletion operations, the honeypot will be gone, so handle accordingly
        if verb == "delete":
            return {
                "message": msg,
                "honeypot": hp.to_dict(),
            }
        
        # For other operations, refresh details
        hp.get_honeypot_details(hp.honeypot_name)  # refresh
        return {
            "message": msg,
            "honeypot": hp.to_dict(),
        }
    except Exception as exc:
        _err(exc)


@router.post("/{name}/start")
async def start(name: str):
    return _do("start", name, "Honeypot started successfully")


@router.post("/{name}/stop")
async def stop(name: str):
    return _do("stop", name, "Honeypot stopped successfully")


@router.post("/{name}/restart")
async def restart(name: str):
    return _do("restart", name, "Honeypot restarted successfully")


@router.delete("/{name}")
async def delete(name: str):
    return _do("delete", name, "Honeypot deleted successfully")

###############################################################################
# metadata
###############################################################################
@router.get("/types", response_model=List[str])
async def types():
    return HoneypotConfig.types()


@router.get("/types/{honeypot_type}/config")
async def type_cfg(honeypot_type: str):
    try:
        return HoneypotConfig.get(honeypot_type)
    except Exception as exc:
        _err(exc)

###############################################################################
# Honeypot Authentication Details
###############################################################################
@router.get("/types/{honeypot_type}/auth-details")
async def get_honeypot_auth_details(honeypot_type: str):
    """Retrieve authentication details and banner from a honeypot's config file."""
    try:
        # Check if honeypot type exists
        if not HoneypotConfig.exists(honeypot_type):
            _err(HoneypotTypeNotFoundError(f"Unknown honeypot type: {honeypot_type}"))
        
        # Get the config file path
        config_path = Path(Honeypot.BASE_DIR) / "honeypots" / honeypot_type / "config.yaml"
        
        if not config_path.exists():
            _err(HTTPException(
                status_code=404, 
                detail=f"Config file for honeypot type '{honeypot_type}' not found"
            ))
        
        # Load the YAML file
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
        except yaml.YAMLError:
            _err(HTTPException(
                status_code=500, 
                detail=f"Error parsing config file for honeypot type '{honeypot_type}'"
            ))
        
        # Extract authentication details and banner
        response_data = {}
        
        # Add authentication if available
        if 'authentication' in config:
            response_data['authentication'] = config['authentication']
            
        # Add banner if available
        if 'banner' in config:
            response_data['banner'] = config['banner']
            
        # Return empty object if no relevant data found
        if not response_data:
            _err(HTTPException(
                status_code=404,
                detail=f"No authentication details or banner found for honeypot type '{honeypot_type}'"
            ))
            
        return response_data
            
    except Exception as exc:
        _err(exc)

###############################################################################
# Filtered honeypot listing
###############################################################################
@router.get("/type/{honeypot_type}", response_model=List[HoneypotResponse])
async def list_honeypots_by_type(honeypot_type: str):
    """Get all honeypots of a specific type (e.g., ssh, ftp)."""
    try:
        # First check if the honeypot type is valid
        if not HoneypotConfig.exists(honeypot_type):
            _err(HoneypotTypeNotFoundError(f"Unknown honeypot type: {honeypot_type}"))
        
        # Filter containers by both service label and type label
        ids = _list_ids(
            "label=service=hive-honeypot-manager", 
            f"label=hive.type={honeypot_type}"
        )
        
        # Convert to response objects
        honeypots = _hp_responses(ids)
        
        # Return 404 if no honeypots found for this type
        if not honeypots:
            _err(HTTPException(
                status_code=404, 
                detail=f"No honeypots of type '{honeypot_type}' found in the system"
            ))
            
        return honeypots
    except Exception as exc:
        _err(exc)


@router.get("/status/{status}", response_model=List[HoneypotResponse])
async def list_honeypots_by_status(status: str):
    """Get all honeypots with a specific status (e.g., running, exited, stopped)."""
    try:
        # Validate status values
        valid_statuses = ["running", "stopped", "exited", "created", "configured"]
        if status not in valid_statuses:
            _err(HTTPException(
                status_code=400,
                detail=f"Invalid status value. Must be one of: {', '.join(valid_statuses)}"
            ))
        
        # Get all honeypot IDs
        all_ids = _list_ids("label=service=hive-honeypot-manager")
        
        # Filter by status manually since Podman doesn't directly support status filtering
        # across all container states through the CLI in a consistent way
        all_honeypots = _hp_responses(all_ids)
        filtered_honeypots = [hp for hp in all_honeypots if hp.status == status]
        
        # Return 404 if no honeypots found with this status
        if not filtered_honeypots:
            _err(HTTPException(
                status_code=404,
                detail=f"No honeypots with status '{status}' found in the system"
            ))
            
        return filtered_honeypots
    except Exception as exc:
        _err(exc)
