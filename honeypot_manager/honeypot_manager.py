import podman
from honeypot_manager.Honeypot import Honeypot

class HoneypotManager:
    _url = 'unix:///tmp/podman.sock'
    _client = podman.PodmanClient(base_url=_url)

    @staticmethod
    def fetch_all_honeypots(self):
        honeypot_list = []
        try:
            # Filter containers with owner=hive label
            containers = HoneypotManager._client.containers.list(filters={'label': 'owner=hive'})
            for container in containers:
                honeypot = Honeypot()
                honeypot.get_honeypot_details(container.id)
                honeypot_list.append(honeypot)
            return honeypot_list
        except Exception as e:
            print(f"Error fetching honeypots: {e}")
            return []

    @staticmethod
    def fetch_all_honeypots_by_type(self, honeypot_type: str):
        honeypot_list = []
        try:
            # Filter containers with owner=hive label and type
            containers = HoneypotManager._client.containers.list(
                filters={'label': 'owner=hive', 'hive.type': honeypot_type}
            )
            for container in containers:
                honeypot = Honeypot()
                honeypot.get_honeypot_details(container.id)
                honeypot_list.append(honeypot)
            return honeypot_list
        except Exception as e:
            print(f"Error fetching honeypots by type: {e}")
            return []

    @staticmethod
    def fetch_all_honeypots_by_status(self, honeypot_status: str):
        try:
            honeypot_list = []
            containers = HoneypotManager._client.containers.list(
                filters={'label': 'owner=hive','status': honeypot_status}
            )
            for container in containers:
                honeypot = Honeypot()
                honeypot.get_honeypot_details(container.id)
                honeypot_list.append(honeypot)
            return honeypot_list
        except Exception as e:
            print(f"Error fetching honeypots by status: {e}")
            return []