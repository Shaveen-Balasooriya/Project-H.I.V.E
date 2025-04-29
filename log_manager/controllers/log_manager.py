from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
from typing import Dict, Any

from models.OpenSearch_Manager import OpenSearchManager
from models.NATS_Server import NATS_Server_Subprocess
from models.Log_Collector import Log_Collector_Subprocess

router = APIRouter()

# Request body model
class CreateServicesRequest(BaseModel):
    """
    Request body model for creating services.
    
    Attributes:
        admin_password: Password for the OpenSearch admin user
    """
    admin_password: str

# Instantiate managers
opensearch_manager = OpenSearchManager()
nats_manager = NATS_Server_Subprocess()
log_collector_manager = Log_Collector_Subprocess()

# ...existing code...
@router.post("/create-services")
async def create_services(request: CreateServicesRequest) -> Dict[str, str]:
    """
    Create all necessary services including OpenSearch, Dashboard, NATS server, and Log Collector.
    
    Args:
        request: Request body containing admin password for OpenSearch
        
    Returns:
        Dict containing a success message
        
    Raises:
        HTTPException: If service creation fails
    """
    # try:
    #     opensearch_exists = opensearch_manager.get_status()
    #     nats_exists = nats_manager.get_status()
    #     log_collector_exists = log_collector_manager.get_status()
        
    #     if opensearch_exists or nats_exists or log_collector_exists:
    #         existing_services = []
    #         if opensearch_exists:
    #             existing_services.append("OpenSearch")
    #         if nats_exists:
    #             existing_services.append("NATS Server")
    #         if log_collector_exists:
    #             existing_services.append("Log Collector")
                
    #         existing_services_str = ", ".join(existing_services)
    #         raise HTTPException(
    #             status_code=400, 
    #             detail=f"Cannot create services. One or more containers already exist: {existing_services_str}. Please delete existing services first."
    #         )
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     # If error occurs during status check, log it but continue with container creation
    #     print(f"Warning: Error checking service status: {str(e)}")

    try:
        opensearch_manager.create_opensearch_container(admin_password=request.admin_password)
        opensearch_manager.create_dashboard_container()
        nats_manager.create_container()
        log_collector_manager.create_container(admin_password=request.admin_password)
        return {"message": "All services created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service creation failed: {str(e)}")

@router.post("/start-services")
async def start_services() -> Dict[str, str]:
    """
    Start all services: OpenSearch, Dashboard, NATS server, and Log Collector.
    
    Returns:
        Dict containing a success message
        
    Raises:
        HTTPException: If starting services fails
    """
    try:
        opensearch_manager.start_services()
        nats_manager.start_container()
        time.sleep(5)
        log_collector_manager.start_container()
        return {"message": "All services started successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service start failed: {str(e)}")

@router.post("/stop-services")
async def stop_services() -> Dict[str, str]:
    """
    Stop all services: OpenSearch, Dashboard, NATS server, and Log Collector.
    
    Returns:
        Dict containing a success message
        
    Raises:
        HTTPException: If stopping services fails
    """
    try:
        opensearch_manager.stop_services()
        nats_manager.stop_container()
        log_collector_manager.stop_container()
        return {"message": "All services stopped successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service stop failed: {str(e)}")

@router.delete("/delete-services")
async def delete_services() -> Dict[str, str]:
    """
    Delete all services: OpenSearch, Dashboard, NATS server, and Log Collector.
    
    This operation is destructive and will remove all containers.
    
    Returns:
        Dict containing a success message
        
    Raises:
        HTTPException: If deleting services fails
    """
    try:
        opensearch_manager.delete_containers()
        nats_manager.delete_container()
        log_collector_manager.delete_container()
        return {"message": "All services deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service delete failed: {str(e)}")

@router.get("/status-services")
async def status_services() -> Dict[str, Any]:
    """
    Get the status of all services: OpenSearch, Dashboard, NATS server, and Log Collector.
    
    Returns:
        Dict containing the status of each service
        
    Raises:
        HTTPException: If retrieving service status fails
    """
    try:
        return {
            "opensearch_and_dashboard": opensearch_manager.get_status(),
            "nats_server": nats_manager.get_status(),
            "log_collector": log_collector_manager.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service status failed: {str(e)}")
