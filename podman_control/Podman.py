import podman

class Podman:
    url = 'unix:///tmp/podman.sock'
    image = 'H.I.V.E-Image'

    def __init__(self) -> None:
        self.client = podman.PodmanClient(base_url=Podman.url)

    def check_config(self):
        if self.client.ping() and self.client.images.exists(Podman.image):
            return True
        elif self.client.ping() and not self.client.images.exists(Podman.image):
            try:
                print("Image does not exist. Creating image...")
                self._create_image()
                return True
            except Exception as e:
                print(f"Error creating image: {e}")
                return False
        else:
            print("Podman is not running.")
            return False

    def _create_image(self) -> None:
        image = 'H.I.V.E-Image'
        try:
            with open('Dockerfile', "rb") as f:
                self.client.images.build(
                    fileobj=f,
                    tag=image,
                    rm=True,
                )
                print(f"Image '{image}' built successfully.")
        except Exception as e:
            print(f"Error building image '{image}': {e}")
