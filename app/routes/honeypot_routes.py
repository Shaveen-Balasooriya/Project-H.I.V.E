# app/routes/honeypot_routes.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
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
        if not honeypots:
            return []
        return honeypots
    except Exception as e:
        print(f'Error fetching honeypots: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Failed to retrieve honeypots: {str(e)}')

@router.get("/status/{status}", response_model=List[HoneypotResponse])
async def get_honeypots_by_status(status: str):
    """Get honeypots by status"""
    try:
        honeypots = HoneypotController.get_honeypots_by_status(status)
        return honeypots
    except Exception as e:
        print(f'Error fetching honeypots by status: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Failed to retrieve honeypots: {str(e)}')

@router.get("/type/{type}", response_model=List[HoneypotResponse])
async def get_honeypots_by_type(honeypot_type: str):
    """Get honeypots by type"""
    try:
        honeypots = HoneypotController.get_honeypots_by_type(honeypot_type)
        return honeypots
    except Exception as e:
        print(f'Error fetching honeypots by type: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Failed to retrieve honeypots: {str(e)}')

@router.get("/{honeypot_id}", response_model=HoneypotResponse)
async def get_honeypot_by_id(honeypot_id: str):
    """Get a honeypot by ID"""
    try:
        honeypot = HoneypotController.get_honeypot_by_id(honeypot_id)
        if not honeypot:
            raise HTTPException(status_code=404, detail="Honeypot not found")
        return honeypot
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to retrieve honeypot: {str(e)}')

@router.post("/", response_model=HoneypotResponse)
async def create_honeypot(honeypot_data: HoneypotCreate):
    """Create a new honeypot"""
    try:
        honeypot = HoneypotController.create_honeypot(honeypot_data)
        if not honeypot:
            raise HTTPException(status_code=400, detail="Failed to create honeypot")
        return honeypot
    except Exception as e:
        print(f'Error creating honeypot: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Failed to create honeypot: {str(e)}')

@router.post("/{honeypot_id}/start", response_model=HoneypotResponse)
async def start_honeypot(honeypot_id: str):
    """Start a honeypot"""
    try:
        honeypot = HoneypotController.start_honeypot(honeypot_id)
        if not honeypot:
            raise HTTPException(status_code=404, detail="Honeypot not found or failed to start")
        return honeypot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to start honeypot: {str(e)}')

@router.post("/{honeypot_id}/stop", response_model=HoneypotResponse)
async def stop_honeypot(honeypot_id: str):
    """Stop a honeypot"""
    try:
        honeypot = HoneypotController.stop_honeypot(honeypot_id)
        if not honeypot:
            raise HTTPException(status_code=404, detail="Honeypot not found or failed to stop")
        return honeypot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to stop honeypot: {str(e)}')

@router.post("/{honeypot_id}/restart", response_model=HoneypotResponse)
async def restart_honeypot(honeypot_id: str):
    """Restart a honeypot"""
    try:
        honeypot = HoneypotController.restart_honeypot(honeypot_id)
        if not honeypot:
            raise HTTPException(status_code=404, detail="Honeypot not found or failed to restart")
        return honeypot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to restart honeypot: {str(e)}')

@router.delete("/{honeypot_id}", response_model=Dict[str, Any])
async def delete_honeypot(honeypot_id: str):
    """Delete a honeypot"""
    try:
        success = HoneypotController.delete_honeypot(honeypot_id)
        if not success:
            raise HTTPException(status_code=404, detail="Honeypot not found or failed to delete")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to delete honeypot: {str(e)}')