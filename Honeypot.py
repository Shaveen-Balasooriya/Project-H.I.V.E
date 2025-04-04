import podman
import os

class Honeypot:
    _url = 'unix:///tmp/podman.sock'

    def __init__(self, honeypot_type: str, honeypot_port: int, honeypot_cpu_limit: int = 100000,
                 honeypot_cpu_quota: int = 50000, honeypot_memory_limit: str = '512m',
                 honeypot_memory_swap_limit: str = '512m') -> None:


        self.honeypot_type = honeypot_type
        self.honeypot_port = honeypot_port
        self.honeypot_cpu_limit = honeypot_cpu_limit
        self.honeypot_cpu_quota = honeypot_cpu_quota
        self.honeypot_memory_limit = honeypot_memory_limit
        self.honeypot_memory_swap_limit = honeypot_memory_swap_limit

        self.honeypot_id = None
        self.image = f'hive-{self.honeypot_type}-image'
        self.honeypot_name = f'hive-{self.honeypot_type}-{self.honeypot_port}'
        self.honeypot_status = None
        self._path_to_honeypot = os.path.join('honeypots', self.honeypot_type)
        self._honeypot_config_path = os.path.join(self._path_to_honeypot, 'config.yaml')

        self._client = podman.PodmanClient(base_url=Honeypot._url)

    def create_honeypot(self) -> bool:
        try:
            if any(container.name == self.honeypot_name for container in self._client.containers.list()):
                return False
            if not any(image.tags[0] == self.image for image in self._client.images.list()):
                if not self._build_image():
                    return False
            if not self._build_container():
                return False
            return True
        except Exception as e:
            print(f"Error creating honeypot: {e}")  # Change to properly log the error
            return False




    def start_honeypot(self):
        ...
    def restart_honeypot(self):
        ...
    def stop_honeypot(self):
        ...
    def remove_honeypot(self):
        ...
    def get_honeypot_status(self):
        ...
    def get_honeypot_details(self):
        ...
    def _build_image(self) -> Exception | bool:
        try:
            self._client.images.build(
                path=self._path_to_honeypot,
                dockerfile='Dockerfile',
                tag=self.image,
                rm=True)
            return True
        except Exception as e:
            print('Error building image:', e) # Change to properly log the error
            return False

    def _build_container(self) -> bool:
        try:
            self._client.containers.create(
                image=self.image,
                name=self.honeypot_name,
                detach=True,
                ports={'22/tcp': self.honeypot_port},
                labels={
                    'hive.type': self.honeypot_type,
                    'hive.port': str(self.honeypot_port),
                },
                volumes={
                    self._honeypot_config_path: {
                        'bind': 'app/config.yaml',
                        'mode': 'rw'
                    }
                },
                hostname=self.honeypot_name,
                cpu_limit=self.honeypot_cpu_limit,
                cpu_quota=self.honeypot_cpu_quota,
                memory=self.honeypot_memory_limit,
                memory_swap=self.honeypot_memory_swap_limit,
                security_opt=['no-new-privileges'],
                restart_policy={'Name': 'always'}
            )
            return True
        except Exception as e:
            print('Error building container:', e) # Change to properly log the error
            return False