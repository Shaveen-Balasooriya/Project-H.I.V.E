import subprocess
import time
import shutil
import os
from typing import Optional, List, Dict, Any

class OpenSearchManager:
    """
    Manages OpenSearch and OpenSearch Dashboard containers using Podman.
    
    This class provides methods to create, start, stop, and manage OpenSearch 
    and OpenSearch Dashboard containers in a pod network configuration.
    """
    
    def __init__(self):
        """Initialize the OpenSearchManager with default configuration values."""
        self.volume_name = "hive-opensearch-data"
        self.network_name = "hive-net"
        self.pod_name = "hive-opensearch-pod"
        self.opensearch_container = "hive-opensearch-node"
        self.dashboard_container = "hive-opensearch-dash"
        self.opensearch_image = "docker.io/opensearchproject/opensearch:latest"
        self.dashboard_image = "docker.io/opensearchproject/opensearch-dashboards:latest"
        # Minimum required disk space in GB
        self.min_disk_space_gb = 8
        # self.admin_password = "Strong_Password123!"

    def _run_command(self, command: List[str]) -> Optional[str]:
        """
        Run a shell command and return its output.
        
        Args:
            command: List of command arguments to execute
            
        Returns:
            The command output as a string or None if the command fails
        """
        print(f"[Running] {' '.join(command)}")
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(result.stdout)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[Error] Command failed: {' '.join(command)}")
            print(e.stderr)
            return None

    def _check_disk_space(self) -> bool:
        """
        Check if there's enough disk space available for OpenSearch.
        
        OpenSearch requires at least 8GB of free disk space to function properly.
        This method checks if the available disk space meets or exceeds this requirement.
        
        Returns:
            True if enough disk space is available, False otherwise
        """
        try:
            # Get the directory where the volume will be stored
            # For Podman, this is typically in /var/lib/containers/storage/volumes
            volume_dir = "/var/lib/containers/storage/volumes"
            if not os.path.exists(volume_dir):
                # If the directory doesn't exist, check the current directory
                volume_dir = "."
                
            # Get disk usage stats
            disk_stats = shutil.disk_usage(volume_dir)
            
            # Convert bytes to GB for easier comparison
            free_space_gb = disk_stats.free / (1024 * 1024 * 1024)
            
            print(f"[Info] Available disk space: {free_space_gb:.2f} GB")
            
            if free_space_gb < self.min_disk_space_gb:
                print(f"[Error] Not enough disk space. OpenSearch requires at least {self.min_disk_space_gb} GB, but only {free_space_gb:.2f} GB available.")
                return False
                
            return True
        except Exception as e:
            print(f"[Error] Failed to check disk space: {str(e)}")
            return False

    def _create_volume(self) -> bool:
        """
        Create a Podman volume for OpenSearch data persistence.
        
        The volume will only be created if it doesn't already exist.
        
        Returns:
            True if volume exists or was created successfully, False otherwise
        """
        existing_volumes = self._run_command(["podman", "volume", "ls", "--format", "{{.Name}}"])
        if existing_volumes and self.volume_name in existing_volumes.splitlines():
            print(f"[✓] Volume '{self.volume_name}' already exists.")
            return True
        
        result = self._run_command(["podman", "volume", "create", self.volume_name])
        if result is not None:
            print(f"[✓] Volume '{self.volume_name}' created.")
            return True
        return False

    def _create_network(self) -> bool:
        """
        Create a Podman network for the containers.
        
        The network will only be created if it doesn't already exist.
        
        Returns:
            True if network exists or was created successfully, False otherwise
        """
        existing_networks = self._run_command(["podman", "network", "ls", "--format", "{{.Name}}"])
        if existing_networks and self.network_name in existing_networks.splitlines():
            print(f"[✓] Network '{self.network_name}' already exists.")
            return True
        
        result = self._run_command(["podman", "network", "create", self.network_name])
        if result is not None:
            print(f"[✓] Network '{self.network_name}' created.")
            return True
        return False

    def _create_pod(self) -> bool:
        """
        Create a Podman pod for hosting the OpenSearch containers.
        
        The pod will only be created if it doesn't already exist.
        
        Returns:
            True if pod exists or was created successfully, False otherwise
        """
        existing_pods = self._run_command(["podman", "pod", "ls", "--format", "{{.Name}}"])
        if existing_pods and self.pod_name in existing_pods.splitlines():
            print(f"[✓] Pod '{self.pod_name}' already exists.")
            return True
        
        result = self._run_command(["podman", "pod", "create", "--name", self.pod_name, "--network", self.network_name, "-p", "5601:5601"])
        if result is not None:
            print(f"[✓] Pod '{self.pod_name}' created.")
            return True
        return False

    def _pull_images(self) -> bool:
        """
        Pull the latest OpenSearch and OpenSearch Dashboard images from Docker Hub.
        
        Returns:
            True if images were pulled successfully, False otherwise
        """
        opensearch_result = self._run_command(["podman", "pull", self.opensearch_image])
        dashboard_result = self._run_command(["podman", "pull", self.dashboard_image])
        
        return opensearch_result is not None and dashboard_result is not None

    def create_opensearch_container(self, admin_password: str) -> bool:
        """
        Create the OpenSearch container with the specified admin password.
        
        This method ensures all prerequisites (images, network, pod, volume) 
        are created before creating the container.
        
        Args:
            admin_password: The password for the OpenSearch admin user
            
        Returns:
            True if container exists or was created successfully, False otherwise
        """
        # Check if there's enough disk space
        if not self._check_disk_space():
            return False
            
        # Check if container already exists
        existing_containers = self._run_command(["podman", "ps", "-a", "--format", "{{.Names}}"])
        if existing_containers and self.opensearch_container in existing_containers.splitlines():
            print(f"[✓] OpenSearch container '{self.opensearch_container}' already exists.")
            return True
        
        # Create prerequisites in sequential order
        if not self._pull_images():
            print("[✗] Failed to pull required images.")
            return False
            
        if not self._create_network():
            print("[✗] Failed to create network.")
            return False
            
        if not self._create_pod():
            print("[✗] Failed to create pod.")
            return False
            
        if not self._create_volume():
            print("[✗] Failed to create volume.")
            return False
        
        # Create the container
        result = self._run_command([
            "podman", "create",
            "--name", self.opensearch_container,
            "--pod", self.pod_name,
            "--volume", f"{self.volume_name}:/usr/share/opensearch/data",
            "--env", "discovery.type=single-node",
            "--env", f"OPENSEARCH_INITIAL_ADMIN_PASSWORD={admin_password}",
            "--env", "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g",
            "--memory", "2g",
            "--cpus", "2",
            "--security-opt", "no-new-privileges",
            self.opensearch_image
        ])
        
        if result is not None:
            print(f"[✓] OpenSearch container '{self.opensearch_container}' created.")
            return True
        return False

    def create_dashboard_container(self) -> bool:
        """
        Create the OpenSearch Dashboard container.
        
        This method ensures all prerequisites are met before creating the container.
        
        Returns:
            True if container exists or was created successfully, False otherwise
        """
        # Check if container already exists
        existing_containers = self._run_command(["podman", "ps", "-a", "--format", "{{.Names}}"])
        if existing_containers and self.dashboard_container in existing_containers.splitlines():
            print(f"[✓] Dashboard container '{self.dashboard_container}' already exists.")
            return True
            
        # Check if pod exists (needed for dashboard container)
        if not self._create_pod():
            print("[✗] Failed to create pod needed for dashboard container.")
            return False
        
        # Create the container
        result = self._run_command([
            "podman", "create",
            "--name", self.dashboard_container,
            "--pod", self.pod_name,
            "--env", "OPENSEARCH_HOSTS=https://localhost:9200",
            "--memory", "1g",
            "--cpus", "1",
            "--security-opt", "no-new-privileges",
            self.dashboard_image
        ])
        
        if result is not None:
            print(f"[✓] Dashboard container '{self.dashboard_container}' created.")
            return True
        return False

    def start_services(self) -> bool:
        """
        Start the OpenSearch and Dashboard containers.
        
        This will first start the OpenSearch container, wait for it to initialize,
        and then start the Dashboard container.
        
        Returns:
            True if services started successfully, False otherwise
        """
        # Check if there's enough disk space before starting
        if not self._check_disk_space():
            return False
            
        self._run_command(["podman", "start", self.opensearch_container])
        print(f"[✓] OpenSearch container '{self.opensearch_container}' started.")
        time.sleep(15)  # Wait for OpenSearch to initialize
        self._run_command(["podman", "start", self.dashboard_container])
        print(f"[✓] Dashboard container '{self.dashboard_container}' started.")
        return True

    def stop_services(self) -> None:
        """
        Stop the OpenSearch and Dashboard containers.
        
        This will stop the Dashboard container first, then the OpenSearch container.
        """
        self._run_command(["podman", "stop", self.dashboard_container])
        print(f"[✓] Dashboard container '{self.dashboard_container}' stopped.")
        self._run_command(["podman", "stop", self.opensearch_container])
        print(f"[✓] OpenSearch container '{self.opensearch_container}' stopped.")

    def delete_containers(self) -> None:
        """
        Delete the OpenSearch and Dashboard containers and the pod.
        
        This operation is destructive and will remove all containers and the pod.
        """
        self._run_command(["podman", "rm", "-f", self.dashboard_container])
        print(f"[✓] Dashboard container '{self.dashboard_container}' removed.")
        self._run_command(["podman", "rm", "-f", self.opensearch_container])
        print(f"[✓] OpenSearch container '{self.opensearch_container}' removed.")
        self._run_command(["podman", "pod", "rm", "-f", self.pod_name])
        print(f"[✓] Pod '{self.pod_name}' removed.")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the OpenSearch and Dashboard containers.
        
        Returns:
            A dictionary containing the status information for both containers
        """
        print("[✓] Container Status:")
        opensearch_status = self._run_command([
            "podman", "inspect", 
            "-f", "{{.State.Status}}", 
            self.opensearch_container
        ])
        
        dashboard_status = self._run_command([
            "podman", "inspect", 
            "-f", "{{.State.Status}}", 
            self.dashboard_container
        ])
        
        return {
            "opensearch": opensearch_status if opensearch_status else "not found",
            "dashboard": dashboard_status if dashboard_status else "not found"
        }
