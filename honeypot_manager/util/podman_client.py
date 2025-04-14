import podman
from podman.errors import PodmanError


class PodmanClientSingleton:
    _instance = None
    _url = 'unix:///tmp/podman.sock'

    @classmethod
    def get_client(cls):
        """Get or create the Podman client singleton instance"""
        if cls._instance is None:
            try:
                cls._instance = podman.PodmanClient(base_url=cls._url)
            except PodmanError as e:
                raise PodmanError(f"Failed to initialize Podman client: {str(e)}")
        return cls._instance


# Export a function to get the client
def get_podman_client():
    """Get the podman client instance"""
    return PodmanClientSingleton.get_client()