import time
from util.podman_client import PodmanClientSingleton

class Log_Collector(): 

    def __init__(self):
        self._client = PodmanClientSingleton().client
        self._container_name = "hive-log-collector"
        self._network_name = "hive-net"
        self._image_name = "hive-log-collector"

    def __del__(self):
        try:
            PodmanClientSingleton.shutdown()
        except Exception as e:
            print(f"[✗] Error during cleanup: {e}")

    def create_log_collector(self): 
        try:
            if self._client.images.exists(self._image_name):
                print("Image already exists!")
                image = self._client.images.get(self._image_name)
            else:
                image = self._client.images.pull(self._image_name)
                print("Image pulled successfully")

            if self._client.containers.exists(self._container_name):
                print("Container already exists!")
                return True
            else:
                container = self._client.containers.create(
                    image=image,
                    name=self._container_name,
                    hostname=self._container_name,
                    networks={self._network_name: {"aliases": [self._container_name]}},
                    network_mode="bridge",
                    detach=True,
                    labels={
                        "owner": "hive",
                        "hive.type": self._container_name
                    },
                    restart_policy={"Name": "always"},
                    privileged=False,
                    security_opt=["no-new-privileges"]
                )
                container.start()
                print("Container started successfully")
                return True
        except Exception as e:
            print("Error creating log collector container", e)
            return False

    def stop_log_collector(self):
        try:
            if self._client.containers.exists(self._container_name):
                container = self._client.containers.get(self._container_name)
                container.stop()
                print("Log collector stopped successfully")
                container.remove(force=True)
                print("Container removed successfully")
                return True
            else:
                print("Container does not exist!")
                return False
        except Exception as e:
            print("Error stopping log collector", e)
            return False

    def reboot_log_collector(self):
        try:
            if self._client.containers.exists(self._container_name):
                container = self._client.containers.get(self._container_name)
                container.restart()
                print("Log collector rebooted successfully")
                return True
            else:
                print("Container does not exist!")
                return False
        except Exception as e:
            print("Error rebooting log collector", e)
            return False

    def _build_log_collector_image(self):
        try:
            if self._client.images.exists(self._image_name):
                print("Image already exists!")
                return True
            else:
                try:
                    self._client.images.build(
                        path=".",
                        dockerfile="Dockerfile.subscriber",
                        tag=self._image_name,
                        rm=True
                    )
                except Exception as e:
                    print("Error building the image", e)
                    return False
        except Exception as e:
            print("Error in the overall builder ", e)
            return False
        
    def get_log_collector_status(self):
        '''
        Returns the status of the log collector container.
        '''
        try:
            container = self._client.containers.get(self._container_name)
            if container.status == "running":
                return {"status": "running", "name": self._container_name}
            else:
                return {"status": "stopped", "name": self._container_name}
        except Exception as e:
            print("Error getting log collector status", e)
            return {"status": "not found", "name": self._container_name}


if __name__ == "__main__":
    lc = Log_Collector()
    lc.stop_log_collector()
    time.sleep(5)
    lc.create_log_collector()
    time.sleep(15)
    lc.reboot_log_collector()
    time.sleep(5)
    lc.stop_log_collector()