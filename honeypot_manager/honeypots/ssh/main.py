import socket
import threading
import yaml
from SSHServer import SSHServer


def load_config(config_file: str) -> dict:
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)


def main() -> None:
    config = load_config('config.yaml')

    ip_address = config['server']['ip_address']
    port = config['server']['port']

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((ip_address, port))
    server.listen(100)
    print(f"Server listening on {ip_address}:{port}")

    try:
        while True:
            client_sock, client_addr = server.accept()
            print(f"Connection from {client_addr[0]}:{client_addr[1]}")
            ssh_server = SSHServer(config)
            threading.Thread(target=ssh_server.handle_client,
                             args=(client_sock, client_addr)).start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.close()


if __name__ == "__main__":
    main()