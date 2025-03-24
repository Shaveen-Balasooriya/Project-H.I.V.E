import podman

try:
    client = podman.PodmanClient(base_url="tcp://0.0.0.0:8080")
    print(client.info())
except Exception as e:
    print(f"Error: {str(e)}")
