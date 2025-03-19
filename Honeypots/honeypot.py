import socket, paramiko, threading

class SSH_Server(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        print(f"Username: {username}, Password: {password}")
        return paramiko.AUTH_FAILED
    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED

def handle_connection(client_socket, server_key):
    transport = paramiko.Transport(client_socket)
    transport.add_server_key(server_key)
    server = SSH_Server()
    transport.start_server(server=server)

def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', 22))
    server_sock.listen(100)

    server_key = paramiko.RSAKey.generate(2048)
    while True:
        client_socket, addr = server_sock.accept()
        thread = threading.Thread(target=handle_connection, args=(client_socket, server_key))
        thread.start()

if __name__ == '__main__':
    main()