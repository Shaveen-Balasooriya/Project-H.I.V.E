import podman
import os

class Podman:
    url = 'unix:///tmp/podman.sock'
    image = 'H.I.V.E-Image'

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

    def build_image(self, honeypot_type: str) -> bool:
        image = f'H.I.V.E-{honeypot_type.upper()}-Image'

        # Determine the build context directory.
        context_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'honeypots',
            honeypot_type.lower()
        )

        # Use the file named 'Dockerfile' in that directory.
        self.client.images.build(
            path=context_path,  # Set the build context directory
            dockerfile='Dockerfile',  # Specify the Dockerfile name
            tag=image,
            rm=True,
        )

        print(f"Image '{image}' built successfully.")
        return True
