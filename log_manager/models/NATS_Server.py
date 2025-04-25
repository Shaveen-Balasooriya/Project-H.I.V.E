import time
from util.podman_client import PodmanClientSingleton

class NATS_Server:
    def __init__(self):
        self._client = PodmanClientSingleton().client
        self._container_name = "hive-nats-server"
        self._image_name = "docker.io/library/nats:latest"
        self._network_name = "hive-net"
        

    def __del__(self):
        try:
            PodmanClientSingleton.shutdown()
        except Exception as e:
            print(f"[✗] Error during cleanup: {e}")

    def create_nats_server(self):
        '''
        Create and start a NATS server container.
        '''
        image = None
        try:
            if self._client.images.exists(self._image_name):
                print("[✓] NATS server image already exists.")
                image = self._client.images.get(self._image_name)
            else:
                image = self._client.images.pull(self._image_name)
                print(f"[✓] NATS server image pulled: {self._image_name}")

            if self._client.containers.exists(self._container_name):
                print("[✓] NATS server container already exists.")
                return True
            else:
                container = self._client.containers.create(
                    image=image,
                    name=self._container_name,
                    hostname=self._container_name,
                    command=["--js", "-m", "8222"],  # explicitly enable monitoring
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
                print(f"[✓] Container 'hive-nats-server' started successfully.")
                return True
        except Exception as e:
            print(f"[✗] Failed to run container 'hive-nats-server': {e}")
            return False

    def stop_nats_server(self):
        '''
        Stops the NATS server container.
        '''
        try:

            if not self._client.containers.exists("hive-nats-server"):
                print("[✓] NATS server container does not exist.")
                return
            else:
                print("[✓] NATS server container exists.")
                container = self._client.containers.get("hive-nats-server")
                container.stop()
                container.remove(force=True)
            print("[✓] NATS server container stopped and removed.")
        except Exception as e:
            print(f"[✗] Failed to stop NATS server: {e}")

    def get_nats_server_status(self):
        try:
            container = self._client.containers.get(self._container_name)
            if container.status == "running":
                return {"status": "running", "name": self._container_name}
            else:
                return {"status": "stopped", "name": self._container_name}
        except Exception as e:
            print(f"[✗] Error getting NATS server status: {e}")
            return {"status": "error", "name": self._container_name}



if __name__ == "__main__":
    nats_server = NATS_Server()
    if not nats_server.create_nats_server():
        print("[✗] Failed to create NATS server.")
    else:
        print("[✓] NATS server is running.")

    # time.sleep(10)
    # print("[✓] Stopping NATS server...")
    # nats_server.stop_nats_server()