# app/models/honeypot_manager.py
import podman
import logging
from typing import List
from app.models.honeypot import Honeypot

logger = logging.getLogger(__name__)

class HoneypotManager:
    _url = 'unix:///tmp/podman.sock'
    _client = podman.PodmanClient(base_url=_url)

    @staticmethod
    def fetch_all_honeypots() -> List[Honeypot]:
        honeypot_list = []
        try:
            # Filter containers with owner=hive label
            containers = HoneypotManager._client.containers.list(all=True, filters={'label': 'owner=hive'})
            for container in containers:
                honeypot = Honeypot()
                honeypot.get_honeypot_details(container.id)
                honeypot_list.append(honeypot)
            return honeypot_list
        except Exception as e:
            logger.error(f"Error fetching honeypots: {e}")
            return []

    @staticmethod
    def fetch_all_honeypots_by_type(honeypot_type: str) -> List[Honeypot]:
        honeypot_list = []
        try:
            # Filter containers with owner=hive label and type
            containers = HoneypotManager._client.containers.list(
                all=True,
                filters={'label': [f'owner=hive', f'hive.type=ssh']}
            )
            for container in containers:
                honeypot = Honeypot()
                honeypot.get_honeypot_details(container.id)
                honeypot_list.append(honeypot)
            return honeypot_list
        except Exception as e:
            logger.error(f"Error fetching honeypots by type: {e}")
            return []

    @staticmethod
    def fetch_all_honeypots_by_status(honeypot_status: str) -> List[Honeypot]:
        try:
            honeypot_list = []
            # Fixed the filter structure
            containers = HoneypotManager._client.containers.list(
                all=True if honeypot_status.lower() == 'exited' else False,
                filters={'label': 'owner=hive', 'status': honeypot_status}
            )
            for container in containers:
                honeypot = Honeypot()
                honeypot.get_honeypot_details(container.id)
                honeypot_list.append(honeypot)
            return honeypot_list
        except Exception as e:
            logger.error(f"Error fetching honeypots by status: {e}")
            return []

    @staticmethod
    def get_honeypot_by_id(honeypot_id: str) -> Honeypot | None:
        """Get a honeypot by ID"""
        try:
            honeypot = Honeypot()
            honeypot.get_honeypot_details(honeypot_id)
            if honeypot.honeypot_id:
                return honeypot
            return None
        except Exception as e:
            logger.error(f"Error getting honeypot by ID: {e}")
            return None