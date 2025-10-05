import subprocess

class HivePod:
    
    _pod_name: str = "hive-log-service"
    
    def create_pod(self):
        try:
            subprocess.run(['podman', 'pod', 'create', '--name', self._pod_name, '--hostname', self._pod_name, '--network', 'hive'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"Pod '{self._pod_name}' created successfully.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print("Pod for HIVE may already exist")
            else:
                print(f"Error creating pod: {e}")
                raise
    def start_pod(self):
        try:
            subprocess.run(['podman', 'pod', 'start', self._pod_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"Pod '{self._pod_name}' started successfully.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"Pod for HIVE does not exist")
            else:
                print(f"Error starting pod: {e}")
                raise

    def restart_pod(self):
        try:
            subprocess.run(['podman', 'pod', 'restart', self._pod_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"Pod '{self._pod_name}' restarted successfully.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"Pod for HIVE does not exist")
            else:
                print(f"Error restarting pod: {e}")
                raise

    def stop_pod(self):
        try:
            subprocess.run(['podman', 'pod', 'stop', self._pod_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"Pod '{self._pod_name}' stopped successfully.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"Pod for HIVE does not exist")
            else:
                print(f"Error stopping pod: {e}")
                raise

    def delete_pod(self):
        try:
            subprocess.run(['podman', 'pod', 'rm', self._pod_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"Pod '{self._pod_name}' deleted successfully.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                print(f"Pod for HIVE does not exist")
            elif e.returncode == 125:
                print("Pod for HIVE is running with running containers and cannot be removed")
            else:
                print(f"Error deleting pod: {e}")
                raise