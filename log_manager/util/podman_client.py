import podman
from podman.errors import PodmanError


class PodmanClientSingleton:
    _instance = None
    _url = 'unix:////run/user/1000/podman/podman.sock'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PodmanClientSingleton, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'client'):
            self.client = podman.PodmanClient(base_url=self._url)
            print("[✓] Podman client initialized.")
        else:
            print("[~] Podman client already initialized, using existing instance.")

    
    @classmethod
    def shutdown(cls):
        if cls._instance is not None and hasattr(cls._instance, 'client'):
            cls._instance.client.close()
            cls._instance = None
            print("[✓] Podman client shut down manually.")
        else:
            print("[✗] Podman client is already shut down or not initialized.")

    def __del__(self):
        try:
            if hasattr(self, 'client'):
                self.client.close()
                print("[✓] Podman client connection closed and singleton reset.")
        except Exception as e:
            print(f"[✗] Error during cleanup: {e}")