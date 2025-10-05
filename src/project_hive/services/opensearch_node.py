import subprocess

class OpenSearchNode:
    
    _name: str = "hive-opensearch-node"
    _image: str = "docker.io/opensearchproject/opensearch:latest"
    
    def create_opensearch_node(self, password: str):
        try:
            subprocess.run(['podman', 'create', '--pod', 'hive-log-service', '--name', self._name, '-q', '--volume', 'hive-data-volume:/usr/share/opensearch/data', '--restart', 'always', '--security-opt', 'no-new-privileges', '--label', 'owner=hive', '--env', 'discovery.type=single-node', '--env', f'OPENSEARCH_INITIAL_ADMIN_PASSWORD=\'{password}\'', '--env', 'OPENSEARCH_JAVA_OPTS="-Xms1g -Xmx1g"', '--memory', '2g', '--cpus', '2', self._image], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print("OpenSearch Node for HIVE may already exist")
            else:
                print(f"Error creating OpenSearch Node: {e}")
                raise

    def start_opensearch_node(self):
        try:
            subprocess.run(['podman', 'start', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"OpenSearch Node for HIVE does not exist")
            else:
                print(f"Error starting OpenSearch Node: {e}")
                raise

    def check_opensearch_node(self):
        try:
            state = subprocess.run(['podman', 'container', 'inspect', self._name, '--format={{.State.Status}}'], capture_output=True, text=True, check=True)
            print(f"OpenSearch Node '{self._name}' exists and is {state.stdout.strip('\n')}")
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"OpenSearch Node '{self._name}' does not exist")
            else:
                print(f"Error checking OpenSearch Node: {e}")
                raise
    
    def restart_opensearch_node(self):
        try:
            subprocess.run(['podman', 'restart', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"OpenSearch Node for HIVE does not exist")
            else:
                print(f"Error restarting OpenSearch Node: {e}")
                raise
    
    def stop_opensearch_node(self):
        try:
            subprocess.run(['podman', 'stop', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 125:
                print(f"OpenSearch Node for HIVE does not exist")
            else:
                print(f"Error stopping OpenSearch Node: {e}")
                raise
    
    def delete_opensearch_node(self):
        try:
            subprocess.run(['podman', 'rm', self._name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                print(f"OpenSearch Node for HIVE does not exist")
            elif e.returncode == 2:
                print(f"OpenSearch Node for HIVE is running and cannot be removed")
            else:
                print(f"Error deleting OpenSearch Node: {e}")
                raise
