import socket
import paramiko
import threading


class SSH_Server(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        print(f"Username: {username}, Password: {password}")
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED


def handle_connection(client_socket, server_key):
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(server_key)
        server = SSH_Server()
        transport.start_server(server=server)
        channel = transport.accept(20)  # Wait up to 20 seconds for authentication
        if channel is not None:
            channel.close()
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        client_socket.close()


# Create a single socket and reuse it
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 2222))
server_socket.listen(100)

print("SSH honeypot running on port 2222...")

server_key = paramiko.RSAKey.generate(2048)
while True:
    try:
        client_socket, addr = server_socket.accept()
        print(f"Connection from: {addr[0]}:{addr[1]}")
        thread = threading.Thread(target=handle_connection, args=(client_socket, server_key))
        thread.daemon = True
        thread.start()
    except Exception as e:
        print(f"Error accepting connection: {e}")
        break

# Clean up
server_socket.close()