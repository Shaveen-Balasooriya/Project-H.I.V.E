import podman
import os

class Podman:
    url = 'unix:///tmp/podman.sock'

    def __init__(self) -> None:
        self.client = podman.PodmanClient(base_url=Podman.url)
        try:
            self.client.ping()
        except Exception as e:
            print(f"Error connecting to Podman: {e}")

    # def _create_image(self) -> None:
    #     image = 'H.I.V.E-Image'
    #     try:
    #         with open('Dockerfile', "rb") as f:
    #             self.client.images.build(
    #                 fileobj=f,
    #                 tag=image,
    #                 rm=True,
    #             )
    #             print(f"Image '{image}' built successfully.")
    #     except Exception as e:
    #         print(f"Error building image '{image}': {e}")

    def build_image(self, honeypot_type: str) -> None:
        image = f'h.i.v.e-image-{honeypot_type.lower()}'
        dockerfile_path = os.path.join('honeypots', honeypot_type)

        # Check if the image already exists
        if self.client.images.exists(image):
            print(f"Image '{image}' already exists.")
        else:
            try:
                print('Building image...')
                # Build from the current directory with the Dockerfile path specified
                self.client.images.build(
                    path=dockerfile_path, # Path to the Dockerfile directory
                    dockerfile='Dockerfile', # Name of the Dockerfile
                    tag=image,
                    rm=True,
                )
                print(f"Image '{image}' built successfully.")
            except PermissionError:
                print("Permission denied. Please run with sudo.")
            except Exception as e:
                print(f"Error building image: {e}")