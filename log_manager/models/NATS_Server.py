import subprocess
from typing import List, Optional

class NATS_Server_Subprocess:
    """
    Manages a NATS server container using Podman.
    
    This class provides methods to create, start, stop, and manage a NATS server
    container for message queue functionality.
    """
    
    def __init__(self):
        """Initialize the NATS server manager with default configuration values."""
        self.network_name = "hive-net"
        self.container_name = "hive-nats-server"
        self.image_name = "docker.io/library/nats:latest"
        self.alias = "hive-nats-server"

    def _run_command(self, cmd_list: List[str]) -> None:
        """
        Run a shell command and handle exceptions.
        
        Args:
            cmd_list: List of command arguments to execute
        
        Raises:
            subprocess.CalledProcessError: If the command execution fails
        """
        print(f"Running command: {' '.join(cmd_list)}")
        subprocess.run(cmd_list, check=True)

    def ensure_network_exists(self) -> None:
        """
        Ensure that the required network exists, creating it if necessary.
        
        The network will only be created if it doesn't already exist.
        """
        result = subprocess.run(["podman", "network", "exists", self.network_name], capture_output=True)
        if result.returncode != 0:
            self._run_command(["podman", "network", "create", self.network_name])
        else:
            print(f"[✓] Network '{self.network_name}' already exists.")

    def pull_image(self) -> None:
        """Pull the latest NATS server image from Docker Hub."""
        self._run_command(["podman", "pull", self.image_name])

    def create_container(self) -> None:
        """
        Create the NATS server container.
        
        This method ensures the required network exists, pulls the latest image,
        and creates the container if it doesn't already exist.
        """
        self.ensure_network_exists()
        self.pull_image()
        
        result = subprocess.run(["podman", "container", "exists", self.container_name], capture_output=True)
        if result.returncode == 0:
            print(f"[✓] Container '{self.container_name}' already exists.")
            return

        self._run_command([
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
        ])
        
        self._run_command([
            "podman", "network", "connect",
            "--alias", self.alias,
            self.network_name,
            self.container_name
        ])
        print(f"[✓] Container '{self.container_name}' created and connected to network '{self.network_name}'.")

    def start_container(self) -> None:
        """
        Start the NATS server container.
        
        Raises:
            subprocess.CalledProcessError: If the start operation fails
        """
        self._run_command(["podman", "start", self.container_name])

    def stop_container(self) -> None:
        """
        Stop the NATS server container.
        
        Raises:
            subprocess.CalledProcessError: If the stop operation fails
        """
        self._run_command(["podman", "stop", self.container_name])

    def delete_container(self) -> None:
        """
        Delete the NATS server container.
        
        This operation is destructive and will remove the container.
        
        Raises:
            subprocess.CalledProcessError: If the deletion fails
        """
        self._run_command(["podman", "rm", "-f", self.container_name])

    def get_status(self) -> str:
        """
        Get the status of the NATS server container.
        
        Returns:
            A string indicating the current status of the container
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
