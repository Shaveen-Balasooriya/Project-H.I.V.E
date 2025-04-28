import subprocess
import os
import sys

class Log_Collector_Subprocess:
    def __init__(self):
        self.network_name = "hive-net"
        self.container_name = "hive-log-collector"
        self.image_name = "hive-log-collector"
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # <-- only one ..
        self.dockerfile_dir = os.path.join(self.project_root, "log_collector")
        self.alias = "hive-log-collector"

    def _run_command(self, cmd_list):
        print(f"Running command: {' '.join(cmd_list)}")
        subprocess.run(cmd_list, check=True)

    def ensure_network_exists(self):
        result = subprocess.run(["podman", "network", "exists", self.network_name], capture_output=True)
        if result.returncode != 0:
            self._run_command(["podman", "network", "create", self.network_name])
        else:
            print(f"[✓] Network '{self.network_name}' already exists.")

    def build_image(self):
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


    def create_container(self):
        self.ensure_network_exists()
        self.build_image()

        result = subprocess.run(["podman", "container", "exists", self.container_name], capture_output=True)
        if result.returncode == 0:
            print(f"[✓] Container '{self.container_name}' already exists.")
            return

        self._run_command([
            "podman", "create",
            "--name", self.container_name,
            "--hostname", self.container_name,
            "--network", "bridge",
            "--env", "NATS_URL=nats://hive-nats-server:4222",
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

    def start_container(self):
        self._run_command(["podman", "start", self.container_name])

    def stop_container(self):
        self._run_command(["podman", "stop", self.container_name])

    def delete_container(self):
        self._run_command(["podman", "rm", "-f", self.container_name])

    def get_status(self):
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

if __name__ == "__main__":
    log_collector = Log_Collector_Subprocess()
    log_collector.create_container()
    log_collector.start_container()
    log_collector.get_status()
