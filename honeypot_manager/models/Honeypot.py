import podman
import os
import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple

from podman.errors import PodmanError
from util.exceptions import (HoneypotContainerError, HoneypotImageError,
                             HoneypotExistsError, HoneypotError,
                             HoneypotPrivilegedPortError, HoneypotTypeNotFoundError)
from util.podman_client import get_podman_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HoneypotConfig:
    """Configuration class for different honeypot types that loads from external YAML file"""
    
    CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   "config", "honeypot_configs.yaml")
    
    # Default configurations to use as fallback
    DEFAULT_CONFIGS = {
        "ssh": {
            "ports": {"22/tcp": "honeypot_port"},
            "volumes": [],
            "passive_ports": None
        },
        "ftp": {
            "ports": {"21/tcp": "honeypot_port"},
            "volumes": ["malware", "logs"],
            "passive_ports": [60000, 60100]
        }
    }
    
    _configs = None
    _last_modified = 0
    
    @classmethod
    def load_configs(cls) -> Dict:
        """Load honeypot configurations from YAML file or use defaults if file not found"""
        try:
            # Check if file exists
            if not os.path.exists(cls.CONFIG_FILE_PATH):
                logger.warning(f"Configuration file {cls.CONFIG_FILE_PATH} not found. Using default configurations.")
                return cls.DEFAULT_CONFIGS
                
            # Check if file has been modified since last load
            current_modified = os.path.getmtime(cls.CONFIG_FILE_PATH)
            if cls._configs is not None and current_modified <= cls._last_modified:
                # Return cached configs if file hasn't changed
                return cls._configs
            
            # Load and parse the YAML file
            with open(cls.CONFIG_FILE_PATH, 'r') as f:
                configs = yaml.safe_load(f)
                
            # Store the configs and last modified time
            cls._configs = configs
            cls._last_modified = current_modified
            logger.info(f"Loaded honeypot configurations from {cls.CONFIG_FILE_PATH}")
            return configs
            
        except Exception as e:
            logger.error(f"Error loading honeypot configurations: {e}")
            logger.warning("Falling back to default configurations")
            return cls.DEFAULT_CONFIGS
    
    @classmethod
    def get_config(cls, honeypot_type: str) -> Dict:
        """Get configuration for specific honeypot type"""
        configs = cls.load_configs()
        if honeypot_type not in configs:
            logger.error(f"Honeypot type '{honeypot_type}' not found in configuration")
            raise HoneypotTypeNotFoundError(f"Honeypot type '{honeypot_type}' not found in configuration")
        return configs[honeypot_type]
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available honeypot types from configuration"""
        configs = cls.load_configs()
        return list(configs.keys())

    @classmethod
    def type_exists(cls, honeypot_type: str) -> bool:
        """Check if a honeypot type exists in the configuration"""
        configs = cls.load_configs()
        return honeypot_type in configs


class Honeypot:
    _url = 'unix:///tmp/podman.sock'
    _client = podman.PodmanClient(base_url=_url)
    
    # Base directory for honeypots
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def __init__(self) -> None:
        self.honeypot_id = None
        self.honeypot_name = None
        self.honeypot_port = None
        self.honeypot_image = None
        self.honeypot_status = None
        self.honeypot_type = None
        self._network_name = "hive-net"

    @staticmethod
    def get_client() -> podman.PodmanClient:
        return get_podman_client()
    
    @staticmethod
    def get_available_honeypot_types() -> List[str]:
        """Return list of available honeypot types from configuration"""
        return HoneypotConfig.get_available_types()

    def create_honeypot(self, honeypot_type: str, honeypot_port: int, honeypot_cpu_limit: int = 100000,
                 honeypot_cpu_quota: int = 50000, honeypot_memory_limit: str = '512m',
                 honeypot_memory_swap_limit: str = '512m') -> bool:
        """Create a new honeypot"""
        try:
            # Validate the honeypot type exists in configuration
            if not HoneypotConfig.type_exists(honeypot_type):
                raise HoneypotTypeNotFoundError(f"Honeypot type '{honeypot_type}' not found in configuration")
            
            self.validate_port(honeypot_port)

            self.honeypot_status = None
            self.honeypot_type = honeypot_type
            self.honeypot_port = honeypot_port
            self.honeypot_name = f'hive-{self.honeypot_type}-{self.honeypot_port}'
            _honeypot_image = f'hive-{self.honeypot_type}-image'
            
            # Use absolute path for honeypot directory
            _path_to_honeypot = os.path.join(self.BASE_DIR, 'honeypots', self.honeypot_type)
            
            # Check if honeypot directory exists
            if not os.path.exists(_path_to_honeypot):
                logger.error(f"Honeypot directory not found: {_path_to_honeypot}")
                raise FileNotFoundError(f"Honeypot directory not found: {_path_to_honeypot}")
                
            _honeypot_config_path = os.path.abspath(os.path.join(_path_to_honeypot, 'config.yaml'))

            if self._honeypot_exist():
                raise HoneypotExistsError('Honeypot already exists')

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
                    raise HoneypotImageError('Failed to build image for the honeypot')
        except FileNotFoundError as e:
            logger.error(f"File not found error: {str(e)}")
            raise HoneypotError(f"File not found: {str(e)}")
        except (HoneypotError, HoneypotExistsError, HoneypotContainerError, HoneypotImageError, HoneypotTypeNotFoundError) as e:
            raise HoneypotError(str(e))
        except PodmanError as e:
            raise PodmanError(str(e))

    def _honeypot_exist(self) -> bool:
        """Check if a honeypot with the same name already exists"""
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
        """Build the honeypot container image"""
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

    def _get_port_mapping(self) -> Dict[str, int]:
        """
        Get the port mapping for the honeypot based on its type
        """
        config = HoneypotConfig.get_config(self.honeypot_type)
        port_mapping = {}
        
        # Map main ports
        for container_port, port_var in config.get("ports", {}).items():
            port_mapping[container_port] = self.honeypot_port
        
        # Map passive ports if applicable
        passive_ports = config.get("passive_ports")
        if passive_ports and isinstance(passive_ports, list) and len(passive_ports) == 2:
            passive_port_start, passive_port_end = passive_ports
            for passive_port in range(passive_port_start, passive_port_end + 1):
                port_mapping[f'{passive_port}/tcp'] = passive_port
                
        # If no specific mapping is found, use a default
        if not port_mapping:
            port_mapping = {'22/tcp': self.honeypot_port}  # Default to SSH port
            
        return port_mapping
    
    def _get_volume_mapping(self, honeypot_config_path: str) -> Dict[str, Dict[str, str]]:
        """
        Get the volume mapping for the honeypot based on its type
        """
        # Base config volume is always present
        volumes = {
            honeypot_config_path: {
                'bind': '/app/config.yaml',
                'mode': 'rw'
            }
        }
        
        # Get additional volumes based on honeypot type
        honeypot_dir = os.path.join(self.BASE_DIR, 'honeypots', self.honeypot_type)
        config = HoneypotConfig.get_config(self.honeypot_type)
        
        for volume_name in config.get("volumes", []):
            volume_dir = os.path.abspath(os.path.join(honeypot_dir, volume_name))
            os.makedirs(volume_dir, exist_ok=True)
            volumes[volume_dir] = {
                'bind': f'/app/{volume_name}',
                'mode': 'rw'
            }
            
        return volumes

    def _build_container(self, honeypot_cpu_limit,
                         honeypot_cpu_quota, honeypot_memory_limit,
                         honeypot_memory_swap_limit, honeypot_config_path, _image) -> bool:
        """Build the honeypot container with the specified configuration"""
        try:
            # Get dynamic port mapping based on honeypot type
            port_mapping = self._get_port_mapping()
            
            # Get dynamic volume mapping based on honeypot type
            volumes = self._get_volume_mapping(honeypot_config_path)
            
            # Create the container
            container = self.get_client().containers.create(
                image=_image,
                name=self.honeypot_name,
                detach=True,
                ports=port_mapping,
                labels={
                    'owner': 'hive',
                    'hive.type': self.honeypot_type,
                    'hive.port': str(self.honeypot_port),
                },
                volumes=volumes,
                hostname=self.honeypot_name,
                networks={self._network_name: {"aliases": [self.honeypot_name]}},
                network_mode="bridge",
                cpu_period=honeypot_cpu_limit,
                cpu_quota=honeypot_cpu_quota,
                mem_limit=honeypot_memory_limit,
                memswap_limit=honeypot_memory_swap_limit,
                security_opt=['no-new-privileges'],
                environment={
                    'NATS_URL': 'nats://hive-nats-server:4222'
                },
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