from fastapi import APIRouter, HTTPException
from models.NATS_Server import NATS_Server
from models.Log_Collector import Log_Collector

router = APIRouter()
nats = NATS_Server()
collector = Log_Collector()

@router.post("/start")
async def start_all():
    """
    Start both the NATS server and the log collector.
    """
    ok_nats = nats.create_nats_server()
    ok_col = collector.create_log_collector()
    if not (ok_nats and ok_col):
        raise HTTPException(status_code=500, detail="Failed to start one or more services.")
    return {
        "nats_server_started": ok_nats,
        "log_collector_started": ok_col
    }

@router.post("/stop")
async def stop_all():
    """
    Stop both the NATS server and the log collector.
    """
    try:
        nats.stop_nats_server()
        collector.stop_log_collector()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping services: {e}")
    return {"stopped": ["nats_server", "log_collector"]}

@router.post("/reboot")
async def reboot_collector():
    """
    Restart only the log collector container.
    """
    ok = collector.reboot_log_collector()
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to reboot log collector.")
    return {"log_collector_rebooted": ok}

@router.get("/status")
async def get_status():
    """
    Get the status of the NATS server and log collector.
    """
    nats_status = nats.get_nats_server_status()
    collector_status = collector.get_log_collector_status()
    return {
        "nats_server": nats_status,
        "log_collector": collector_status
    }