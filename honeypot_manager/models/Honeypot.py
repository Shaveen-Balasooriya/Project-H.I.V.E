import podman
import os
from typing import Dict, Any

from podman.errors import PodmanError
from honeypot_manager.util.exceptions import (HoneypotContainerError, HoneypotImageError,
                                              HoneypotExistsError, HoneypotError,
                                              HoneypotPrivilegedPortError)
from honeypot_manager.util.podman_client import get_podman_client

class Honeypot:
    _url = 'unix:///tmp/podman.sock'
    _client = podman.PodmanClient(base_url=_url)

    def __init__(self) -> None:
        self.honeypot_id = None
        self.honeypot_name = None
        self.honeypot_port = None
        self.honeypot_image = None
        self.honeypot_status = None
        self.honeypot_type = None

    @staticmethod
    def get_client() -> podman.PodmanClient:
        return get_podman_client()

    def create_honeypot(self, honeypot_type: str, honeypot_port: int, honeypot_cpu_limit: int = 100000,
                 honeypot_cpu_quota: int = 50000, honeypot_memory_limit: str = '512m',
                 honeypot_memory_swap_limit: str = '512m') -> bool:
        try:
            self.validate_port(honeypot_port)

            self.honeypot_status = None
            self.honeypot_type =  honeypot_type
            self.honeypot_port = honeypot_port
            self.honeypot_name = f'hive-{self.honeypot_type}-{self.honeypot_port}'
            _honeypot_image = f'hive-{self.honeypot_type}-image'
            _path_to_honeypot = os.path.join('.', 'honeypots', self.honeypot_type)
            _honeypot_config_path = os.path.abspath(os.path.join(_path_to_honeypot,'config.yaml'))

            if self._honeypot_exist():
                raise Exception('Honeypot already exists')

            if self.get_client().images.exists(_honeypot_image):
                if self._build_container(honeypot_cpu_limit,
                         honeypot_cpu_quota, honeypot_memory_limit,
                         honeypot_memory_swap_limit, _honeypot_config_path, _honeypot_image):
                    return True
                else:
                    raise HoneypotContainerError('Failed to create Honeypot container')
            else:
                if self._build_image(_path_to_honeypot, _honeypot_image):
                    self.create_honeypot(honeypot_type, honeypot_port, honeypot_cpu_limit,
                                         honeypot_cpu_quota, honeypot_memory_limit,
                                         honeypot_memory_swap_limit)
                    return True
                else:
                    raise HoneypotImageError('Failed to image for the honeypot')
        except (HoneypotError, HoneypotExistsError, HoneypotContainerError, HoneypotImageError) as e:
            raise HoneypotError(str(e))
        except PodmanError as e:
            raise PodmanError(str(e))

    def _honeypot_exist(self) -> bool:
        try:
            return self.get_client().containers.exists(self.honeypot_name)
        except HoneypotError as e:
            raise HoneypotError(str(e))

    @staticmethod
    def validate_port(port: int) -> bool:
        """
        Validate if a port can be used by the current user.

        Args:
            port: The port number to validate

        Returns:
            bool: True if the port can be used

        Raises:
            HoneypotPrivilegedPortError: When the port is privileged (<1024) and the current user doesn't have permission
        """
        if port < 1024 and os.geteuid() != 0:
            # Running as non-root and trying to use a privileged port
            raise HoneypotPrivilegedPortError(
                f"Cannot use privileged port {port}. Please use a port number >= 1024 or configure your system to allow rootless containers to use privileged ports."
            )
        return True

    def _build_image(self, _path_to_honeypot: str, _image_name) -> bool:
        try:
            self.get_client().images.build(
                path=_path_to_honeypot,
                dockerfile='Dockerfile',
                tag=_image_name,
                rm=True)
            return True
        except HoneypotImageError as e:
            raise HoneypotImageError(str(e))
        except PermissionError as e:
            raise PermissionError(str(e))
        except PodmanError as e:
            raise PodmanError(str(e))

    def _build_container(self, honeypot_cpu_limit,
                         honeypot_cpu_quota, honeypot_memory_limit,
                         honeypot_memory_swap_limit, honeypot_config_path, _image) -> bool:
        try:
            container = self.get_client().containers.create(
                image=_image,
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
        except HoneypotContainerError as e:
            raise HoneypotContainerError(str(e))
        except PermissionError as e:
            raise PermissionError(str(e))
        except PodmanError as e:
            raise PodmanError(str(e))

    def start_honeypot(self) -> bool:
        """
        Start a honeypot container.

        Returns:
            bool: True if the container was started successfully

        Raises:
            HoneypotPrivilegedPortError: When trying to use a privileged port (<1024) without proper permissions
            HoneypotContainerError: For other container operation failures
        """
        try:
            self.get_client().containers.get(self.honeypot_name).start()
            return True
        except Exception as e:
            error_msg = str(e)

            # Check for privileged port error
            if ("rootlessport cannot expose privileged port" in error_msg or
                "permission denied" in error_msg) and str(self.honeypot_port) in error_msg:
                raise HoneypotPrivilegedPortError(
                    f"Cannot use privileged port {self.honeypot_port}. Please use a port number >= 1024 or configure your system to allow rootless containers to use privileged ports."
                )
            # Check for container not found
            elif "no such container" in error_msg.lower():
                raise HoneypotContainerError(f"Container not found: {self.honeypot_name}")
            # Check for already running
            elif "container already running" in error_msg.lower():
                # This could be handled as a non-error if desired
                return True
            # General container error
            else:
                raise HoneypotContainerError(f"Failed to start honeypot: {str(e)}")

    def restart_honeypot(self) -> bool:
        """
        Restart a honeypot container.

        Returns:
            bool: True if the container was restarted successfully

        Raises:
            HoneypotPrivilegedPortError: When trying to use a privileged port (<1024) without proper permissions
            HoneypotContainerError: For other container operation failures
        """
        try:
            self.get_client().containers.get(self.honeypot_name).restart()
            return True
        except Exception as e:
            error_msg = str(e)
            # Check for privileged port error, might occur during restart as well
            if ("rootlessport cannot expose privileged port" in error_msg or
                "permission denied" in error_msg) and str(self.honeypot_port) in error_msg:
                raise HoneypotPrivilegedPortError(
                    f"Cannot use privileged port {self.honeypot_port}. Please use a port number >= 1024 or configure your system to allow rootless containers to use privileged ports."
                )
            elif "no such container" in error_msg.lower():
                raise HoneypotContainerError(f"Container not found: {self.honeypot_name}")
            else:
                raise HoneypotContainerError(f"Failed to restart honeypot: {str(e)}")

    def stop_honeypot(self) -> bool:
        """
        Stop a honeypot container.

        Returns:
            bool: True if the container was stopped successfully

        Raises:
            HoneypotContainerError: For container operation failures
        """
        try:
            self.get_client().containers.get(self.honeypot_name).stop()
            return True
        except Exception as e:
            error_msg = str(e)
            if "no such container" in error_msg.lower():
                raise HoneypotContainerError(f"Container not found: {self.honeypot_name}")
            elif "container not running" in error_msg.lower():
                # Container already stopped, consider this a success
                return True
            else:
                raise HoneypotContainerError(f"Failed to stop honeypot: {str(e)}")

    def delete_honeypot(self) -> bool:
        """
        Delete a honeypot container.

        Returns:
            bool: True if the container was deleted successfully

        Raises:
            HoneypotContainerError: For container operation failures
        """
        try:
            self.get_client().containers.get(self.honeypot_name).remove(timeout=10)
            return True
        except Exception as e:
            error_msg = str(e)
            if "no such container" in error_msg.lower():
                # Container already gone, consider this a success
                return True
            elif "removal of container" in error_msg.lower() and "is already in progress" in error_msg.lower():
                # Removal already in progress
                return True
            else:
                raise HoneypotContainerError(f"Failed to delete honeypot: {str(e)}")

    def get_honeypot_details(self, honeypot_identifier: str):
        """
        Get details of a honeypot by its identifier (name or ID)

        Args:
            honeypot_identifier: The name or ID of the honeypot container

        Returns:
            Honeypot: Self with populated details, or None if not found
        """
        try:
            container = self.get_client().containers.get(honeypot_identifier)
            self.honeypot_id = container.id
            self.honeypot_name = container.name
            self.honeypot_status = container.status
            self.honeypot_type = container.labels.get('hive.type', 'unknown')
            self.honeypot_port = int(container.labels.get('hive.port', '0'))
            self.honeypot_image = str(container.image)
            return self
        except Exception as e:
            error_msg = str(e)
            if "no such container" in error_msg.lower():
                # Return None to indicate container not found
                return None
            else:
                # For other errors, raise a HoneypotError
                raise HoneypotError(f"Error retrieving honeypot details: {str(e)}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "honeypot_id": self.honeypot_id,
            "honeypot_type": self.honeypot_type,
            "honeypot_port": self.honeypot_port,
            "image": self.honeypot_image,
            "honeypot_name": self.honeypot_name,
            "honeypot_status": self.honeypot_status
        }