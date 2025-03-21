import os
import paramiko
import socket
import threading
from paramiko.common import AUTH_SUCCESSFUL, AUTH_FAILED, OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED, OPEN_SUCCEEDED


class SSHHoneypot(paramiko.ServerInterface):
    """
    SSH Honeypot implementation using Paramiko and sockets.
    The honeypot only captures authentication attempts without shell emulation.
    """

    def __init__(self, port: int, banner: str, credentials: list, bind_address: str = "0.0.0.0", key_file: str =
    None) -> None:
        """
        Initialize the SSH honeypot with the given parameters.

        Args:
            port (int): The port number where the honeypot will listen.
            banner (str): The banner message displayed to connecting clients.
            credentials (list): List of (username, password) tuples for authentication.
            bind_address (str, optional): Address to bind the server to. Defaults to "0.0.0.0".
            key_file (str, optional): File to store/load the RSA host key. Defaults to nothing.
        """
        self.port = port
        self.banner = banner
        self.credentials = credentials
        self.bind_address = bind_address

        if key_file is None:
            self.key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ssh_host_key")
        else:
            self.key_file = key_file

        # Private attributes
        self._server_socket = None
        self._host_key = None
        self._is_running = False
        self._server_thread = None

        # Generate or load host key
        self._load_or_generate_host_key()

    def check_auth_password(self, username: str, password: str) -> int:
        """
        Log authentication attempts and optionally allow them based on credentials.

        Args:
            username (str): The username to authenticate.
            password (str): The password to authenticate.

        Returns:
            int: AUTH_SUCCESSFUL if credentials are valid, otherwise AUTH_FAILED.
        """
        print(f"Authentication attempt: {username}:{password}")

        # Check all credentials
        for uname, pwd in self.credentials:
            if uname == username and pwd == password:
                print(f"Successful authentication: {username}:{password}")
                return AUTH_SUCCESSFUL

        print(f"Failed authentication: {username}:{password}")
        return AUTH_FAILED

    def get_allowed_auths(self, username: str) -> str:
        """
        Return the allowed authentication methods.

        Args:
            username (str): The username for which to return allowed authentication methods.

        Returns:
            str: Comma-separated string of allowed authentication methods.
        """
        return "password"  # Only allow password auth

    def check_channel_request(self, kind: str, chanid: int) -> int:
        """
        Validate channel request.

        Args:
            kind (str): The type of channel being requested.
            chanid (int): The ID of the channel being requested.

        Returns:
            int: OPEN_SUCCEEDED for 'session', OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED otherwise.
        """
        if kind == 'session':
            return OPEN_SUCCEEDED
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def deploy(self) -> None:
        """
        Deploy the SSH honeypot by starting the server socket and listener thread.
        """
        if self._is_running:
            print("SSH Honeypot is already running")
            return

        try:
            # Create server socket
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self.bind_address, self.port))
            self._server_socket.listen(5)

            # Start server thread
            self._is_running = True
            self._server_thread = threading.Thread(target=self._accept_connections)
            self._server_thread.daemon = True
            self._server_thread.start()

            print(f"SSH Honeypot deployed and listening on {self.bind_address}:{self.port}")

        except Exception as e:
            print(f"Error deploying SSH Honeypot: {str(e)}")
            self.retract()
            raise

    def retract(self) -> None:
        """
        Safely shut down the SSH honeypot and clean up resources.
        """
        print("Shutting down SSH Honeypot...")
        self._is_running = False

        # Close server socket
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception as e:
                print(f"Error closing server socket: {str(e)}")

        # Wait for server thread to complete
        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=5.0)

        # Clean up
        self._server_socket = None
        self._server_thread = None

        print("SSH Honeypot has been successfully shut down")

    # Private methods
    def _load_or_generate_host_key(self) -> None:
        """
        Load existing host key or generate a new one if it doesn't exist.
        """
        try:
            self._host_key = paramiko.RSAKey(filename=self.key_file)
            print(f"Using existing host key: {self.key_file}")
        except FileNotFoundError:
            print(f"Generating new host key: {self.key_file}")
            self._host_key = paramiko.RSAKey.generate(2048)
            self._host_key.write_private_key_file(self.key_file)

    def _accept_connections(self) -> None:
        """
        Accept incoming connections and handle them in separate threads.
        """
        print("Starting connection acceptance thread")

        while self._is_running:
            try:
                client_socket, addr = self._server_socket.accept()
                print(f"Connection from: {addr[0]}:{addr[1]}")

                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self._is_running:
                    print(f"Error accepting connections: {str(e)}")
                break

        print("Connection acceptance thread terminated")

    def _handle_client(self, client_socket: socket.socket, addr: tuple) -> None:
        """
        Handle client connections and SSH negotiation.
        Only process the authentication, no shell emulation.

        Args:
            client_socket (socket.socket): Client socket connection
            addr (tuple): Client address information
        """
        try:
            # Set up the Paramiko transport
            transport = paramiko.Transport(client_socket)
            transport.set_gss_host(socket.getfqdn(""))

            # Set the server banner
            if self.banner:
                transport.local_version = f"SSH-2.0-{self.banner}"

            # Add server key and start SSH server
            transport.add_server_key(self._host_key)

            # Start the server - this is where authentication happens
            transport.start_server(server=self)

            # Wait for authentication
            channel = transport.accept(20)  # Wait up to 20 seconds for auth

            # We don't need to do anything with the channel once authenticated
            # Just log the successful authentication and close
            if channel is not None:
                print(f"Channel established from {addr[0]}:{addr[1]} - closing connection")
                channel.close()

            # Close the transport
            if transport.is_active():
                transport.close()

        except paramiko.SSHException as e:
            print(f"SSH error from {addr[0]}:{addr[1]}: {str(e)}")
        except Exception as e:
            print(f"Error handling client {addr[0]}:{addr[1]}: {str(e)}")
        finally:
            try:
                client_socket.close()
            finally:
                print(f"Connection closed from {addr[0]}:{addr[1]}")
