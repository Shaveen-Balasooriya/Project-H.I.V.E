import subprocess
from typing import List, Optional, Tuple, Dict, Any

class NATS_Server_Subprocess:
    """
    Manages a NATS server container using Podman.
    
    This class provides methods to create, start, stop, and manage a NATS server
    container for message queue functionality. NATS is a lightweight, high-performance
    messaging system for cloud native applications, microservices, and IoT messaging.
    
    Attributes:
        network_name (str): The name of the network for container communication.
        container_name (str): The name assigned to the NATS server container.
        image_name (str): The Docker image name/tag to pull for the NATS server.
        alias (str): The network alias for the NATS server container.
    """
    
    def __init__(self):
        """
        Initialize the NATS server manager with default configuration values.
        
        Sets up the default network name, container name, image name, and alias
        that will be used for creating and managing the NATS server container.
        """
        self.network_name = "hive-net"
        self.container_name = "hive-nats-server"
        self.image_name = "docker.io/library/nats:latest"
        self.alias = "hive-nats-server"

    def _run_command(self, cmd_list: List[str]) -> bool:
        """
        Run a shell command and handle exceptions.
        
        Args:
            cmd_list: List of command arguments to execute
        
        Returns:
            bool: True if command executed successfully, False otherwise
            
        Notes:
            This is a helper method that prints the command being executed and
            then runs it using subprocess.run with error checking enabled.
        """
        print(f"Running command: {' '.join(cmd_list)}")
        try:
            subprocess.run(cmd_list, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
            return False

    def _ensure_network_exists(self) -> bool:
        """
        Ensure that the required network exists, creating it if necessary.
        
        The network will only be created if it doesn't already exist. This method
        checks for the existence of the network defined by self.network_name and
        creates it if needed.
        
        Returns:
            bool: True if network exists or was successfully created, False otherwise
        """
        result = subprocess.run(["podman", "network", "exists", self.network_name], capture_output=True)
        if result.returncode != 0:
            if self._run_command(["podman", "network", "create", self.network_name]):
                return True
            else:
                print(f"Failed to create network '{self.network_name}'")
                return False
        else:
            print(f"[✓] Network '{self.network_name}' already exists.")
            return True

    def _pull_image(self) -> bool:
        """
        Pull the latest NATS server image from Docker Hub.
        
        This method fetches the Docker image defined by self.image_name from
        the Docker registry to ensure the latest version is available locally.
        
        Returns:
            bool: True if image was successfully pulled, False otherwise
        """
        if self._run_command(["podman", "pull", self.image_name]):
            print(f"[✓] Successfully pulled image '{self.image_name}'")
            return True
        else:
            print(f"Failed to pull image '{self.image_name}'")
            return False

    def create_container(self) -> bool:
        """
        Create the NATS server container.
        
        This method ensures the required network exists, pulls the latest image,
        and creates the container if it doesn't already exist. The container is
        configured with appropriate networking, labels, and NATS-specific settings.
        
        The container is created with JetStream enabled (-js flag) and the monitoring
        port 8222 exposed.
        
        Returns:
            bool: True if container was created successfully, False otherwise
        """
        # Check if network exists or can be created
        if not self._ensure_network_exists():
            print("Failed to ensure network exists, aborting container creation")
            return False
        
        # Pull the image
        if not self._pull_image():
            print("Failed to pull image, aborting container creation")
            return False
        
        # Check if container already exists
        result = subprocess.run(["podman", "container", "exists", self.container_name], capture_output=True)
        if result.returncode == 0:
            print(f"[✓] Container '{self.container_name}' already exists.")
            return True

        # Create container
        if not self._run_command([
            "podman", "create",
            "--name", self.container_name,
            "--hostname", self.container_name,
            "--network", "bridge",
            "--label", f"owner=hive",
            "--label", f"hive.type={self.container_name}",
            "--restart", "always",
            "--security-opt", "no-new-privileges",
            self.image_name,
            "--js", "-m", "8222"
        ]):
            print(f"Failed to create container '{self.container_name}'")
            return False
        
        # Connect container to network
        if not self._run_command([
            "podman", "network", "connect",
            "--alias", self.alias,
            self.network_name,
            self.container_name
        ]):
            print(f"Failed to connect container to network '{self.network_name}'")
            return False
        
        print(f"[✓] Container '{self.container_name}' created and connected to network '{self.network_name}'.")
        return True

    def start_container(self) -> bool:
        """
        Start the NATS server container.
        
        This method starts the existing NATS server container if it has been created.
        
        Returns:
            bool: True if container was started successfully, False otherwise
        """
        return self._run_command(["podman", "start", self.container_name])

    def stop_container(self) -> bool:
        """
        Stop the NATS server container.
        
        This method stops the running NATS server container without removing it.
        The container can be started again with start_container().
        
        Returns:
            bool: True if container was stopped successfully, False otherwise
        """
        return self._run_command(["podman", "stop", self.container_name])

    def delete_container(self) -> bool:
        """
        Delete the NATS server container.
        
        This operation is destructive and will remove the container entirely.
        Any data stored within the container that is not in a persistent volume will be lost.
        
        Returns:
            bool: True if container was deleted successfully, False otherwise
        """
        return self._run_command(["podman", "rm", "-f", self.container_name])

    def get_status(self) -> str:
        """
        Get the status of the NATS server container.
        
        Returns:
            str: A string indicating the current status of the container.
                 Possible values include: "running", "stopped", "exited", 
                 "paused", "created", or "not found".
        
        Notes:
            The method checks the container status via podman inspect command
            and returns a user-friendly message about the current container state.
        """
        try:
            result = subprocess.run(
                ["podman", "inspect", "-f", "{{.State.Status}}", self.container_name],
                capture_output=True, text=True, check=True
            )
            status = result.stdout.strip()
            print(f"[INFO] {self.container_name} is {status}")
            return status
        except subprocess.CalledProcessError:
            print(f"[INFO] {self.container_name} not found.")
            return "not found"
