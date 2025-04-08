# app/models/honeypot.py
import podman
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Honeypot:
    _url = 'unix:///tmp/podman.sock'
    _client = podman.PodmanClient(base_url=_url)

    def __init__(self) -> None:
        self.honeypot_id = None
        self.honeypot_type = None
        self.honeypot_port = None
        self.image = None
        self.honeypot_name = None
        self.honeypot_status = None

    def create_honeypot(self, honeypot_type: str, honeypot_port: int, honeypot_cpu_limit: int = 100000,
                 honeypot_cpu_quota: int = 50000, honeypot_memory_limit: str = '512m',
                 honeypot_memory_swap_limit: str = '512m') -> bool:
        try:
            self.honeypot_status = None
            self.honeypot_port = honeypot_port
            self.honeypot_type = honeypot_type
            self.image = f'hive-{self.honeypot_type}-image'
            self.honeypot_name = f'hive-{self.honeypot_type}-{self.honeypot_port}'
            path_to_honeypot = os.path.join('.', 'honeypots', self.honeypot_type)
            honeypot_config_path = os.path.abspath(os.path.join(path_to_honeypot,'config.yaml'))
            if self._honeypot_exist():
                raise Exception('Honeypot already exists')
            if Honeypot._client.images.exists(self.image):
                if self._build_container(honeypot_cpu_limit, honeypot_cpu_quota,
                                         honeypot_memory_limit, honeypot_memory_swap_limit,
                                         honeypot_config_path):
                    return True
                else:
                    return False
            else:
                if self._build_image(path_to_honeypot):
                    self.create_honeypot(honeypot_type, honeypot_port, honeypot_cpu_limit,
                                         honeypot_cpu_quota, honeypot_memory_limit, honeypot_memory_swap_limit)
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"Error creating honeypot: {e}")
            return False

    def start_honeypot(self):
        try:
            Honeypot._client.containers.get(self.honeypot_name).start()
            self.honeypot_status = Honeypot._client.containers.get(self.honeypot_name).status
            return True
        except Exception as e:
            logger.error(f"Error starting honeypot: {e}")
            return False

    def restart_honeypot(self) -> bool:
        try:
            Honeypot._client.containers.get(self.honeypot_name).restart()
            self.honeypot_status = Honeypot._client.containers.get(self.honeypot_name).status
            return True
        except Exception as e:
            logger.error(f"Error restarting honeypot: {e}")
            return False

    def stop_honeypot(self) -> bool:
        try:
            if self.honeypot_status == 'running':
                Honeypot._client.containers.get(self.honeypot_name).stop(timeout=10)
                self.honeypot_status = Honeypot._client.containers.get(self.honeypot_name).status
                return True
            else:
                logger.info('Honeypot already stopped')
                return True
        except Exception as e:
            logger.error(f"Error stopping honeypot: {e}")
            return False

    def remove_honeypot(self) -> bool:
        try:
            if self.stop_honeypot():
                Honeypot._client.containers.get(self.honeypot_name).remove(timeout=10)
                return True
            else:
                raise Exception(f'Failed to stop honeypot {self.honeypot_name}. Cannot remove.')
        except Exception as e:
            logger.error(f"Error removing honeypot: {e}")
            return False

    def get_honeypot_details(self, honeypot_id: str):
        try:
            container = Honeypot._client.containers.get(honeypot_id)
            self.honeypot_name = container.name
            self.honeypot_id = container.id
            self.honeypot_status = container.status
            self.honeypot_port = int(container.labels.get('hive.port'))
            self.image = container.image
            self.honeypot_type = container.labels.get('hive.type')
        except Exception as e:
            logger.error(f"Error getting honeypot details: {e}")
            return None

    def _build_image(self, path_to_honeypot) -> bool:
        try:
            Honeypot._client.images.build(
                path=path_to_honeypot,
                dockerfile='Dockerfile',
                tag=self.image,
                rm=True)
            return True
        except Exception as e:
            logger.error(f'Error building image: {e}')
            return False

    def _build_container(self, honeypot_cpu_limit, honeypot_cpu_quota, honeypot_memory_limit,
                         honeypot_memory_swap_limit, honeypot_config_path) -> bool:
        try:
            container = Honeypot._client.containers.create(
                image=self.image,
                name=self.honeypot_name,
                detach=True,
                ports={'22/tcp': self.honeypot_port},
                labels={
                    'owner': 'hive',
                    'hive.type': self.honeypot_type,
                    'hive.port': str(self.honeypot_port),
                },
                volumes={
                    honeypot_config_path: {
                        'bind': '/app/config.yaml',
                        'mode': 'rw'
                    }
                },
                hostname=self.honeypot_name,
                cpu_period=honeypot_cpu_limit,
                cpu_quota=honeypot_cpu_quota,
                mem_limit=honeypot_memory_limit,
                memswap_limit=honeypot_memory_swap_limit,
                security_opt=['no-new-privileges'],
                restart_policy={'Name': 'always'}
            )
            self.honeypot_id = container.id
            self.honeypot_status = container.status
            return True
        except Exception as e:
            logger.error(f'Error building container: {e}')
            return False

    def _honeypot_exist(self) -> bool:
        try:
            return self._client.containers.exists(self.honeypot_name)
        except Exception as e:
            logger.error(f"Error checking if container exists: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert honeypot object to dictionary"""
        return {
            "honeypot_id": self.honeypot_id,
            "honeypot_type": self.honeypot_type,
            "honeypot_port": self.honeypot_port,
            "image": str(self.image),
            "honeypot_name": self.honeypot_name,
            "honeypot_status": self.honeypot_status
        }