import subprocess

class HiveVolume:
    
    _name: str = "hive-data-volume"
    
    def create_volume(self):
        try:
            subprocess.run(['podman', 'volume', 'create', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"Volume '{self._name}' created successfully.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"Volume '{self._name}' may already exist")
            else:
                print(f"Error creating volume: {e}")
                raise
    
    def check_volume(self):
        try:
            subprocess.run(['podman', 'volume', 'exists', self._name], check=True)
            print(f"Volume '{self._name}' exists.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                print(f"Volume '{self._name}' does not exist")
            else:
                print(f"Error checking volume: {e}")
                raise
            
    def delete_volume(self):
        try:
            subprocess.run(['podman', 'volume', 'rm', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"Volume '{self._name}' deleted successfully.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                print(f"Volume '{self._name}' does not exist or cannot be removed")
            elif e.returncode == 2:
                print(f"Volume '{self._name}' is in use and cannot be removed")
            else:
                print(f"Error deleting volume: {e}")
                raise