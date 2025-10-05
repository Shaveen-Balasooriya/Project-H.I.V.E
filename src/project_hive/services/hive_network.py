import subprocess

class HiveNetwork:
    
    network_name = "hive"

    def create_network(self):
        try:
            subprocess.run(['podman', 'network', 'create', self.network_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"Network '{self.network_name}' may already exist")
            else:
                print(f"Error creating network: {e}")
                raise

    def check_network(self):
        try:
            subprocess.run(['podman', 'network', 'exists', self.network_name], check=True)
            print(f"Network '{self.network_name}' exists")
            return True
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                print(f"Network '{self.network_name}' does not exist")
                return False
            else:
                print(f"Error checking network: {e}")
                raise

    def delete_network(self):
        try:
            subprocess.run(['podman', 'network', 'rm', self.network_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL ,check=True)
            print(f"Network '{self.network_name}' deleted successfully")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                print(f"Network '{self.network_name}' does not exist or cannot be removed")
            elif e.returncode == 2:
                print(f"Network '{self.network_name}' is in use and cannot be removed")
            else:
                print(f"Error deleting network: {e}")
                raise