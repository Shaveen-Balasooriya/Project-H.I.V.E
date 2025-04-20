from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
import logging
from podman.errors import PodmanError, APIError
from schemas.honeypot import HoneypotCreate, HoneypotResponse
from models.Honeypot import Honeypot, HoneypotConfig
from util.exceptions import (
    HoneypotError, HoneypotExistsError, HoneypotImageError, HoneypotContainerError, 
    HoneypotPrivilegedPortError, HoneypotTypeNotFoundError
)
from util.podman_client import get_podman_client
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(
    prefix="/honeypot-manager",
    tags=["honeypot-manager"],
)

# Error message dictionary for user-friendly messages
ERROR_MESSAGES = {
    HoneypotExistsError: (
        "A honeypot already exists with this configuration", status.HTTP_409_CONFLICT),
    HoneypotImageError: (
        "Could not create the honeypot image. System resources might be insufficient",
        status.HTTP_500_INTERNAL_SERVER_ERROR),
    HoneypotContainerError: (
        "Failed to manage the honeypot container", status.HTTP_500_INTERNAL_SERVER_ERROR),
    HoneypotPrivilegedPortError: (
        "Port permission error: Ports below 1024 require root privileges or special system configuration",
        status.HTTP_400_BAD_REQUEST),
    HoneypotTypeNotFoundError: (
        "Honeypot type not found. Please use one of the available types from the /honeypot-manager/types endpoint",
        status.HTTP_404_NOT_FOUND),
    PodmanError: (
        "Container system error. Please try again later", status.HTTP_500_INTERNAL_SERVER_ERROR),
    APIError: (  # Add handling for APIError specifically
        "Container system API error. Make sure Podman system service is running",
        status.HTTP_500_INTERNAL_SERVER_ERROR),
    PermissionError: (
        "Insufficient permissions to perform this operation", status.HTTP_403_FORBIDDEN),
    FileNotFoundError: (
        "Required files or directories not found", status.HTTP_500_INTERNAL_SERVER_ERROR),
}


def handle_honeypot_error(e: Exception) -> HTTPException:
    """
    Centralized error handler to convert exceptions to user-friendly HTTP exceptions
    """
    error_type = type(e)
    if error_type in ERROR_MESSAGES:
        message, status_code = ERROR_MESSAGES[error_type]
        
        # For type not found error, include more context from the exception
        if error_type == HoneypotTypeNotFoundError:
            # Extract the honeypot type from the error message if available
            message = str(e) if str(e) else message
            # Include list of available types in the error message
            try:
                available_types = Honeypot.get_available_honeypot_types()
                if available_types:
                    message = f"{message}. Available types: {', '.join(available_types)}"
            except Exception:
                # If we can't get available types, just use the default message
                pass
        # For file not found errors, include path information
        elif error_type == FileNotFoundError:
            message = f"File or directory not found: {str(e)}"

    else:
        message = f"An unexpected error occurred: {str(e)}"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    logger.error(f"Honeypot error: {error_type.__name__} - {str(e)}")
    return HTTPException(status_code=status_code, detail=message)


@router.get("/", response_model=List[HoneypotResponse])
async def get_all_honeypots():
    """Get a list of all honeypots in the system"""
    try:
        honeypot_list = []
        containers = get_podman_client().containers.list(all=True, filters={'label': 'owner=hive'})

        for container in containers:
            honeypot = Honeypot()
            honeypot.get_honeypot_details(container.id)
            honeypot_list.append(HoneypotResponse(**honeypot.to_dict()))

        return honeypot_list
    except Exception as e:
        raise handle_honeypot_error(e)


@router.get("/type/{honeypot_type}", response_model=List[HoneypotResponse])
async def get_honeypots_by_type(honeypot_type: str):
    """Get all honeypots of a specific type"""
    try:
        # Validate that the type exists
        if not HoneypotConfig.type_exists(honeypot_type):
            raise HoneypotTypeNotFoundError(f"Honeypot type '{honeypot_type}' not found in configuration")

        honeypot_list = []
        containers = get_podman_client().containers.list(all=True, filters={'label': f'hive.type='
                                                                                  f'{honeypot_type}'})

        # Process the containers that match the filter
        for container in containers:
            honeypot = Honeypot()
            honeypot.get_honeypot_details(container.id)
            honeypot_list.append(HoneypotResponse(**honeypot.to_dict()))

        # Add debugging to help identify issues
        logger.info(f"Found {len(containers)} containers of type {honeypot_type}")

        return honeypot_list
    except Exception as e:
        logger.error(f"Error getting honeypots by type: {str(e)}")
        raise handle_honeypot_error(e)


@router.get("/status/{honeypot_status}", response_model=List[HoneypotResponse])
async def get_honeypots_by_status(honeypot_status: str):
    """Get all honeypots with a specific status"""
    try:
        honeypot_list = []
        containers = get_podman_client().containers.list(
            all=True,
            filters={'label': 'owner=hive', 'status': honeypot_status}
        )

        for container in containers:
            honeypot = Honeypot()
            honeypot.get_honeypot_details(container.id)
            honeypot_list.append(HoneypotResponse(**honeypot.to_dict()))

        return honeypot_list
    except Exception as e:
        raise handle_honeypot_error(e)

@router.get("/name/{honeypot_name}", response_model=HoneypotResponse)
async def get_honeypot(honeypot_name: str):
    """Get details for a specific honeypot"""
    try:
        honeypot = Honeypot()
        result = honeypot.get_honeypot_details(honeypot_name)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Honeypot not found"
            )
        return HoneypotResponse(**honeypot.to_dict())
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        raise handle_honeypot_error(e)


@router.post("/", response_model=HoneypotResponse, status_code=status.HTTP_201_CREATED)
async def create_honeypot(honeypot_data: HoneypotCreate):
    """Create a new honeypot"""
    try:
        # Validate honeypot type exists before attempting creation
        if not HoneypotConfig.type_exists(honeypot_data.honeypot_type):
            raise HoneypotTypeNotFoundError(f"Honeypot type '{honeypot_data.honeypot_type}' not found in configuration")
       
        # Validate honeypot directory exists
        honeypot_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'honeypots', 
            honeypot_data.honeypot_type
        )
        if not os.path.exists(honeypot_path):
            raise FileNotFoundError(f"Honeypot directory '{honeypot_path}' does not exist")
            
        honeypot = Honeypot()
        success = honeypot.create_honeypot(
            honeypot_type=honeypot_data.honeypot_type,
            honeypot_port=honeypot_data.honeypot_port,
            honeypot_cpu_limit=honeypot_data.honeypot_cpu_limit,
            honeypot_cpu_quota=honeypot_data.honeypot_cpu_quota,
            honeypot_memory_limit=honeypot_data.honeypot_memory_limit,
            honeypot_memory_swap_limit=honeypot_data.honeypot_memory_swap_limit
        )
        honeypot.get_honeypot_details(honeypot.honeypot_name)
        if success:
            return HoneypotResponse(**honeypot.to_dict())
        else:
            raise HoneypotError("Failed to create honeypot")

    except Exception as e:
        if isinstance(e, HoneypotExistsError):
            # Add more context to this specific error
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A honeypot using port {honeypot_data.honeypot_port} already exists. Please use a different port."
            )
        raise handle_honeypot_error(e)


@router.post("/{honeypot_name}/start")
async def start_honeypot(honeypot_name: str):
    """Start a honeypot"""
    try:
        honeypot = Honeypot()
        honeypot.get_honeypot_details(honeypot_name)

        if honeypot.honeypot_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Honeypot not found"
            )

        if honeypot.honeypot_status == "running":
            return {"message": f"Honeypot '{honeypot.honeypot_name}' has already started"}

        success = honeypot.start_honeypot()
        if success:
            return {"message": f"Honeypot started successfully"}
        else:
            raise HoneypotContainerError("Failed to start honeypot")

    except (HoneypotError, HoneypotPrivilegedPortError) as e:
        error = handle_honeypot_error(e)
        raise error
    except HTTPException as e:
        raise e
    except Exception as e:
        raise handle_honeypot_error(e)


@router.post("/{honeypot_name}/stop")
async def stop_honeypot(honeypot_name: str):
    """Stop a honeypot"""
    try:
        honeypot = Honeypot()
        honeypot.get_honeypot_details(honeypot_name)

        if honeypot.honeypot_name is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Honeypot not found"
            )

        if honeypot.honeypot_status == "exited":
            return {"message": f"Honeypot '{honeypot.honeypot_name}' is already stopped"}

        success = honeypot.stop_honeypot()
        if success:
            return {"message": f"Honeypot stopped successfully"}
        else:
            raise HoneypotContainerError("Failed to stop honeypot")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise handle_honeypot_error(e)


@router.post("/{honeypot_name}/restart")
async def restart_honeypot(honeypot_name: str):
    """Restart a honeypot"""
    try:
        honeypot = Honeypot()
        honeypot.get_honeypot_details(honeypot_name)

        if honeypot.honeypot_name is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Honeypot not found"
            )

        success = honeypot.restart_honeypot()
        if success:
            return {"message": "Honeypot restarted successfully"}
        else:
            raise HoneypotContainerError("Failed to restart honeypot")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise handle_honeypot_error(e)


@router.delete("/{honeypot_name}")
async def delete_honeypot(honeypot_name: str):
    """Delete a honeypot"""
    try:
        honeypot = Honeypot()
        honeypot.get_honeypot_details(honeypot_name)

        if honeypot.honeypot_name is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Honeypot not found"
            )

        success = honeypot.delete_honeypot()
        if success:
            return {"message": "Honeypot deleted successfully"}
        else:
            raise HoneypotContainerError("Failed to delete honeypot")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise handle_honeypot_error(e)


@router.get("/types", response_model=List[str])
async def get_honeypot_types():
    """Get a list of all available honeypot types from configuration"""
    try:
        return Honeypot.get_available_honeypot_types()
    except Exception as e:
        raise handle_honeypot_error(e)


@router.get("/types/{honeypot_type}/config")
async def get_honeypot_type_config(honeypot_type: str):
    """Get the configuration details for a specific honeypot type"""
    try:
        if not HoneypotConfig.type_exists(honeypot_type):
            raise HoneypotTypeNotFoundError(f"Honeypot type '{honeypot_type}' not found in configuration")
        
        config = HoneypotConfig.get_config(honeypot_type)
        return config
    except Exception as e:
        raise handle_honeypot_error(e)