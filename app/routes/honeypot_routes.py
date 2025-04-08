# app/routes/honeypot_routes.py
from fastapi import APIRouter, HTTPException, Path, Depends
from typing import List

from app.schemas.honeypot import HoneypotCreate, HoneypotResponse
from app.controllers.honeypot_controller import HoneypotController

router = APIRouter(
    prefix="/honeypots",
    tags=["honeypots"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[HoneypotResponse])
async def get_all_honeypots():
    """Get all honeypots"""
    try:
        honeypots = HoneypotController.get_all_honeypots()
        if honeypots is None:
            # Return empty list instead of None
            return []
        return honeypots
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error fetching honeypots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve honeypots: {str(e)}")

@router.get("/type/{honeypot_type}", response_model=List[HoneypotResponse])
async def get_honeypots_by_type(honeypot_type: str = Path(..., description="Type of honeypot to filter by")):
    """Get honeypots by type"""
    return HoneypotController.get_honeypots_by_type(honeypot_type)

@router.get("/status/{status}", response_model=List[HoneypotResponse])
async def get_honeypots_by_status(status: str = Path(..., description="Status to filter by")):
    """Get honeypots by status"""
    return HoneypotController.get_honeypots_by_status(status)

@router.get("/{honeypot_id}", response_model=HoneypotResponse)
async def get_honeypot(honeypot_id: str = Path(..., description="ID of the honeypot to get")):
    """Get a specific honeypot by ID"""
    honeypot = HoneypotController.get_honeypot_by_id(honeypot_id)
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    return honeypot

@router.post("/", response_model=HoneypotResponse, status_code=201)
async def create_honeypot(honeypot_data: HoneypotCreate):
    """Create a new honeypot"""
    try:
        honeypot = HoneypotController.create_honeypot(honeypot_data)
        if not honeypot:
            raise HTTPException(status_code=400, detail="Failed to create honeypot")
        return honeypot
    except Exception as e:
        # Log the error
        print(f"Error creating honeypot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating honeypot: {str(e)}")

@router.post("/{honeypot_id}/start", response_model=HoneypotResponse)
async def start_honeypot(honeypot_id: str = Path(..., description="ID of the honeypot to start")):
    """Start a honeypot"""
    honeypot = HoneypotController.start_honeypot(honeypot_id)
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found or could not be started")
    return honeypot

@router.post("/{honeypot_id}/stop", response_model=HoneypotResponse)
async def stop_honeypot(honeypot_id: str = Path(..., description="ID of the honeypot to stop")):
    """Stop a honeypot"""
    honeypot = HoneypotController.stop_honeypot(honeypot_id)
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found or could not be stopped")
    return honeypot

@router.post("/{honeypot_id}/restart", response_model=HoneypotResponse)
async def restart_honeypot(honeypot_id: str = Path(..., description="ID of the honeypot to restart")):
    """Restart a honeypot"""
    honeypot = HoneypotController.restart_honeypot(honeypot_id)
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found or could not be restarted")
    return honeypot

@router.delete("/{honeypot_id}", status_code=200)
async def delete_honeypot(honeypot_id: str = Path(..., description="ID of the honeypot to delete")):
    """Delete a honeypot"""
    success = HoneypotController.delete_honeypot(honeypot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Honeypot not found or could not be deleted")
    return {"success": True}