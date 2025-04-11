import logging
from typing import List, Optional, Dict, Any

from app.exceptions.honeypot_exceptions import HoneypotError
from app.models.honeypot import Honeypot
from app.models.honeypot_manager import HoneypotManager
from app.schemas.honeypot import HoneypotCreate, HoneypotUpdate

logger = logging.getLogger(__name__)


class HoneypotController:
    """
    Controller handling business logic between API endpoints and data models
    Acts as a service layer
    """

    @staticmethod
    def get_all_honeypots() -> List[Dict[str, Any]]:
        """Get all honeypots"""
        manager = HoneypotManager()
        honeypots = manager.fetch_all_honeypots()
        return [hp.to_dict() for hp in honeypots]

    @staticmethod
    def get_honeypots_by_type(honeypot_type: str) -> List[Dict[str, Any]]:
        """Get honeypots filtered by type"""
        manager = HoneypotManager()
        honeypots = manager.fetch_all_honeypots_by_type(honeypot_type)
        return [hp.to_dict() for hp in honeypots]

    @staticmethod
    def get_honeypots_by_status(status: str) -> List[Dict[str, Any]]:
        """Get honeypots filtered by status"""
        manager = HoneypotManager()
        honeypots = manager.fetch_all_honeypots_by_status(status)
        return [hp.to_dict() for hp in honeypots]

    @staticmethod
    def get_honeypot_by_id(honeypot_id: str) -> Optional[Dict[str, Any]]:
        """Get a single honeypot by ID"""
        manager = HoneypotManager()
        honeypot = manager.get_honeypot_by_id(honeypot_id)
        if honeypot:
            return honeypot.to_dict()
        return None

    @staticmethod
    def create_honeypot(honeypot_data: HoneypotCreate) -> Optional[Dict[str, Any]]:
        """Create a new honeypot"""
        try:
            honeypot = Honeypot()
            success = honeypot.create_honeypot(
                honeypot_type=honeypot_data.honeypot_type,
                honeypot_port=honeypot_data.honeypot_port,
                honeypot_cpu_limit=honeypot_data.honeypot_cpu_limit,
                honeypot_cpu_quota=honeypot_data.honeypot_cpu_quota,
                honeypot_memory_limit=honeypot_data.honeypot_memory_limit,
                honeypot_memory_swap_limit=honeypot_data.honeypot_memory_swap_limit
            )

            if success:
                return honeypot.to_dict()
            return None
        except HoneypotError as e:
            raise

    @staticmethod
    def start_honeypot(honeypot_id: str) -> Optional[Dict[str, Any]]:
        """Start a honeypot"""
        manager = HoneypotManager()
        honeypot = manager.get_honeypot_by_id(honeypot_id)

        if not honeypot:
            return None

        if honeypot.start_honeypot():
            return honeypot.to_dict()
        return None

    @staticmethod
    def stop_honeypot(honeypot_id: str) -> Optional[Dict[str, Any]]:
        """Stop a honeypot"""
        manager = HoneypotManager()
        honeypot = manager.get_honeypot_by_id(honeypot_id)

        if not honeypot:
            return None

        if honeypot.stop_honeypot():
            return honeypot.to_dict()
        return None

    @staticmethod
    def restart_honeypot(honeypot_id: str) -> Optional[Dict[str, Any]]:
        """Restart a honeypot"""
        manager = HoneypotManager()
        honeypot = manager.get_honeypot_by_id(honeypot_id)

        if not honeypot:
            return None

        if honeypot.restart_honeypot():
            return honeypot.to_dict()
        return None

    @staticmethod
    def delete_honeypot(honeypot_id: str) -> bool:
        """Delete a honeypot"""
        manager = HoneypotManager()
        honeypot = manager.get_honeypot_by_id(honeypot_id)

        if not honeypot:
            return False

        return honeypot.remove_honeypot()