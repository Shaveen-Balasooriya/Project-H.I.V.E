import subprocess

class NATSServer:
    
    _name: str = "hive-nats-server"
    _image: str = "docker.io/library/nats:latest"

    def create_nats_server(self):
        try:
            subprocess.run(['podman', 'create', '--pod', 'hive-log-service', '--name', self._name, '-q','--restart', 'always',  '--security-opt', 'no-new-privileges', '--label', 'owner=hive','--label', f'hive.type={self._name}', self._image, '--js', '-m', '8222'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"NATS server '{self._name}' may already exist {e}")
            else:
                print(f"Error creating NATS server: {e}")
                raise
            
    def start_nats_server(self):
        try:
            subprocess.run(['podman', 'start', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"NATS server '{self._name}' does not exist")
            else:
                print(f"Error starting NATS server: {e}")
                raise
    
    def check_nats_server(self):
        try:
            state = subprocess.run(['podman', 'container', 'inspect', self._name, '--format={{.State.Status}}'], capture_output=True, text=True, check=True)
            print(f"NATS server '{self._name}' exists and is {state.stdout.strip('\n')}")
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"NATS server '{self._name}' does not exist")
            else:
                print(f"Error checking NATS server: {e}")
                raise
    
    def restart_nats_server(self):
        try:
            subprocess.run(['podman', 'restart', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"NATS server '{self._name}' does not exist")
            else:
                print(f"Error restarting NATS server: {e}")
                raise
    
    def stop_nats_server(self):
        try:
            subprocess.run(['podman', 'stop', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"NATS server '{self._name}' does not exist")
            else:
                print(f"Error stopping NATS server: {e}")
                raise
    
    def delete_nats_server(self):
        try:
            subprocess.run(['podman', 'rm', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                print(f"NATS server '{self._name}' does not exist or cannot be removed")
            else:
                print(f"Error deleting NATS server: {e}")
                raise