import subprocess
import os
import sys

class Log_Collector_Subprocess:
    """
    A class responsible for managing the log collector container in the H.I.V.E project.
    
    This class handles the lifecycle of the log collector container, including creating
    the required network, building the container image, creating, starting, stopping,
    and deleting the container. It uses podman commands to interact with containers.
    """

    def __init__(self):
        """
        Initialize the Log_Collector_Subprocess with default configuration values.
        
        Sets up container name, image name, network configuration, and directory paths
        needed for building and running the log collector container.
        """
        self.network_name = "hive-net"
        self.container_name = "hive-log-collector"
        self.image_name = "hive-log-collector"
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # <-- only one ..
        self.dockerfile_dir = os.path.join(self.project_root, "log_collector")
        self.alias = "hive-log-collector"

    def _run_command(self, cmd_list):
        """
        Execute a shell command using subprocess.
        
        Args:
            cmd_list (list): List of command arguments to be executed.
            
        Raises:
            subprocess.CalledProcessError: If the command returns a non-zero exit status.
        """
        print(f"Running command: {' '.join(cmd_list)}")
        subprocess.run(cmd_list, check=True)

    def _ensure_network_exists(self):
        """
        Ensure that the required Docker network exists, creating it if necessary.
        
        Checks if the network defined by self.network_name exists and creates it
        if it doesn't.
        
        Returns:
            bool: True if the network exists or was created successfully, False otherwise.
        """
        try:
            result = subprocess.run(["podman", "network", "exists", self.network_name], capture_output=True)
            if result.returncode != 0:
                self._run_command(["podman", "network", "create", self.network_name])
            else:
                print(f"[✓] Network '{self.network_name}' already exists.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[✗] Failed to ensure network exists: {str(e)}")
            return False

    def _build_image(self):
        """
        Build the container image if it doesn't already exist.
        
        Checks if the image defined by self.image_name exists and builds it
        from the Dockerfile.subscriber in the log_collector directory if needed.
        Temporarily changes working directory to the Dockerfile location during build.
        
        Returns:
            bool: True if the image exists or was built successfully, False otherwise.
        """
        try:
            result = subprocess.run(["podman", "image", "exists", self.image_name], capture_output=True)
            if result.returncode != 0:
                print(f"[~] Building image '{self.image_name}'...")
                
                # Change working directory to dockerfile directory
                current_dir = os.getcwd()
                try:
                    os.chdir(self.dockerfile_dir)
                    self._run_command([
                        "podman", "build",
                        "-t", self.image_name,
                        "-f", "Dockerfile.subscriber",
                        "."
                    ])
                    print(f"[✓] Built image '{self.image_name}'.")
                finally:
                    # Always return back to the original directory
                    os.chdir(current_dir)
            else:
                print(f"[✓] Image '{self.image_name}' already exists.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[✗] Failed to build image: {str(e)}")
            return False


    def create_container(self, admin_password):
        """
        Create the log collector container if it doesn't exist.
        
        This method performs the following steps:
        1. Ensures the required network exists
        2. Ensures the container image is built
        3. Creates the container with appropriate settings if it doesn't exist
        4. Connects the container to the hive network with the specified alias
        
        Returns:
            bool: True if the container was created successfully or already exists, False otherwise.
        """
        # Only proceed if both network and image are available
        if not self._ensure_network_exists():
            print("[✗] Failed to create network. Container creation aborted.")
            return False
        
        if not self._build_image():
            print("[✗] Failed to build image. Container creation aborted.")
            return False

        try:
            result = subprocess.run(["podman", "container", "exists", self.container_name], capture_output=True)
            if result.returncode == 0:
                print(f"[✓] Container '{self.container_name}' already exists.")
                return True

            self._run_command([
                "podman", "create",
                "--name", self.container_name,
                "--hostname", self.container_name,
                "--network", "bridge",
                "--env", "NATS_URL=nats://hive-nats-server:4222",
                "--env", "OPENSEARCH_USER=admin",
                "--env", f"OPENSEARCH_PASSWORD={admin_password}",
                "--env", "OPENSEARCH_HOST=https://hive-opensearch-pod:9200",
                "--label", f"owner=hive",
                "--label", f"hive.type={self.container_name}",
                "--restart", "always",
                "--security-opt", "no-new-privileges",
                self.image_name
            ])

            self._run_command([
                "podman", "network", "connect",
                "--alias", self.alias,
                self.network_name,
                self.container_name
            ])
            print(f"[✓] Container '{self.container_name}' created and connected to network '{self.network_name}'.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[✗] Failed to create container: {str(e)}")
            return False

    def start_container(self):
        """
        Start the log collector container.
        
        Uses podman to start the container identified by self.container_name.
        
        Returns:
            bool: True if the container started successfully, False otherwise.
        """
        try:
            self._run_command(["podman", "start", self.container_name])
            return True
        except subprocess.CalledProcessError as e:
            print(f"[✗] Failed to start container: {str(e)}")
            return False

    def stop_container(self):
        """
        Stop the log collector container.
        
        Uses podman to stop the container identified by self.container_name.
        
        Returns:
            bool: True if the container stopped successfully, False otherwise.
        """
        try:
            self._run_command(["podman", "stop", self.container_name])
            return True
        except subprocess.CalledProcessError as e:
            print(f"[✗] Failed to stop container: {str(e)}")
            return False

    def delete_container(self):
        """
        Delete the log collector container.
        
        Uses podman to forcefully remove the container identified by self.container_name.
        
        Returns:
            bool: True if the container was deleted successfully, False otherwise.
        """
        try:
            self._run_command(["podman", "rm", "-f", self.container_name])
            return True
        except subprocess.CalledProcessError as e:
            print(f"[✗] Failed to delete container: {str(e)}")
            return False

    def get_status(self):
        """
        Get the current status of the log collector container.
        
        Returns:
            str: The status of the container (e.g., 'running', 'exited', 'not found').
        
        Raises:
            subprocess.CalledProcessError: If the inspection command fails.
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
