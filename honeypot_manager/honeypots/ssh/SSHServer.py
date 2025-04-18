import os
import paramiko
import threading
import re


class SSHServer(paramiko.ServerInterface):
    def __init__(self, config: dict):
        self.event = threading.Event()
        self.allowed_users = config['authentication']['allowed_users']
        self.ssh_key_path = config['ssh']['key_path']
        self.banner = config['ssh']['banner']
        self._generate_ssh_key()

    def _generate_ssh_key(self):
        """Generate an SSH key if it doesn't already exist."""
        if os.path.exists(self.ssh_key_path):
            print(f"SSH key already exists at {self.ssh_key_path}.")
            return
        try:
            key = paramiko.RSAKey.generate(2048)
            key.write_private_key_file(self.ssh_key_path)
            print(f"Generated new SSH key at {self.ssh_key_path}.")
        except Exception as e:
            print(f"Failed to generate SSH key: {e}")

    def check_channel_request(self, kind, chanid) -> int:
        """Allow only session channels."""
        if kind == 'session':
            print(f"Channel request accepted: {kind}")
            return paramiko.OPEN_SUCCEEDED
        print(f"Channel request rejected: {kind}")
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username) -> str:
        """Specify that only password authentication is allowed."""
        print(f"Authentication attempts allowed for user: {username}")
        return 'password'

    def check_auth_password(self, username, password) -> int:
        """Authenticate the user based on predefined credentials."""
        print(f"Password authentication attempt for user: {username}")
        for user in self.allowed_users:
            if username == user['username'] and password == user['password']:
                print("Authentication successful.")
                return paramiko.AUTH_SUCCESSFUL
        print("Authentication failed.")
        return paramiko.AUTH_FAILED

    def check_channel_shell_request(self, channel) -> bool:
        print("Shell request accepted.")
        channel.send(self.banner + "\n")
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight,
                                  modes) -> bool:
        print(f"PTY request accepted: {term}")
        return True

    def handle_client(self, client, addr):
        client_ip = addr[0]
        print(f'New connection from: {client_ip}')
        transport = None
        try:
            # Initialize SSH transport
            transport = paramiko.Transport(client)
            transport.add_server_key(paramiko.RSAKey(filename=self.ssh_key_path))
            transport.local_version = self.banner  # Set SSH banner

            # Initialize SSHServer with the current instance configuration
            server = SSHServer({
                "authentication": {"allowed_users": self.allowed_users},
                "ssh": {"key_path": self.ssh_key_path, "banner": self.banner},
            })

            # Start the transport server
            try:
                transport.start_server(server=server)
            except paramiko.SSHException:
                print('SSH negotiation failed.')
                transport.close()
                return

            # Wait for a client channel
            chan = transport.accept()
            if chan is None:
                print(f'No channel from {client_ip}.')
                transport.close()
                return

            # Wait for the shell request
            server.event.wait()
            if not server.event.is_set():
                print(f'Client {client_ip} never requested a shell.')
                transport.close()
                return

            # Send welcome banner with proper line breaks
            chan.send("Welcome to Ubuntu 20.04.4 LTS\r\n")
            chan.send("* Documentation:  https://help.ubuntu.com\r\n")
            chan.send("* Management:     https://landscape.canonical.com\r\n")
            chan.send("* Support:        https://ubuntu.com/advantage\r\n\r\n")
            chan.send("Last login: Mon Apr 15 12:34:56 2024 from 192.168.1.100\r\n")
            chan.send("$ ")  # Initial prompt

            # Improved command handling with proper line breaks and input echoing
            buffer = ""
            session_active = True
            while session_active:
                try:
                    # Read input byte by byte
                    byte = chan.recv(1)

                    # Check for connection closure
                    if not byte:
                        break

                    # Convert byte to string
                    char = byte.decode('utf-8')

                    # Handle backspace
                    if ord(char) == 127 or ord(char) == 8:  # Backspace or DEL
                        if buffer:
                            buffer = buffer[:-1]
                            # Erase last character and move cursor back
                            chan.send('\b \b')
                        continue

                    # Send input character back to client to simulate terminal echo
                    chan.send(char.encode('utf-8'))

                    # Accumulate input
                    buffer += char

                    # Check for command completion (Enter key)
                    if char == '\r' or char == '\n':
                        command = buffer.strip()
                        buffer = ""  # Reset buffer

                        # Send a newline to move to next line
                        chan.send('\r\n')

                        # Handle exit commands
                        if command.lower() in ["exit", "quit"]:
                            chan.send("Connection closed.\r\n")
                            chan.close()
                            session_active = False
                            break

                        # Process command
                        print(f'Command received from {client_ip}: {command}')
                        response = self.handle_cmd(command, client_ip)

                        # Send response with proper line breaks
                        lines = response.split('\n')
                        formatted_response = '\r\n'.join(line.strip() for line in lines)
                        chan.send(formatted_response + "\r\n")
                        chan.send("$ ")  # Prompt for next command

                except Exception as e:
                    print(f"Error receiving data from {client_ip}: {e}")
                    break

        except Exception as e:
            print(f'Exception handling connection from {client_ip}: {e}')
        finally:
            if transport:
                transport.close()
            print(f"Connection from {client_ip} closed.")

    def handle_cmd(self, cmd, ip):
        """Handle commands received from clients."""
        response = ""

        # Sanitize and normalize command
        cmd = cmd.strip()

        # Basic command handling with more flexible matching
        if re.match(r'^ls\s*.*$', cmd):
            # Simple, clean ls output
            response = "users.txt\nflag.txt"
        elif re.match(r'^pwd\s*$', cmd):
            response = "/home/root"
        elif cmd == "clear":
            response = ""  # Simulate clear screen
        else:
            response = f"Command '{cmd}' not recognized."

        print(f'Response to {ip}: {response}')
        return response