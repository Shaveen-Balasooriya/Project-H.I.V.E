import os
import datetime
import logging
import paramiko
import threading
import asyncio
from typing import Dict, Any, Tuple
from NATSJetstreamPublisher import NATSJetstreamPublisher

# Logging Setup
LOG_DIR = os.path.abspath('/app/logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'ssh_honeypot.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ssh_honeypot')

class SSHServer(paramiko.ServerInterface):
    def __init__(self, config: Dict[str, Any]):
        self.event = threading.Event()
        self.allowed_users = config.get('authentication', {}).get('allowed_users', [])
        self.ssh_key_path = config.get('ssh', {}).get('key_path', 'ssh_host_rsa_key')
        self.banner = config.get('ssh', {}).get('banner', 'SSH-2.0-OpenSSH_8.2p1')

        self.client_ip = None
        self.client_port = None
        self.session_start = None
        self.session_id = None
        self.authenticated = False
        self.username = None
        self.password = None
        self.executed_commands = []
        self.user_agent = None

        self._generate_ssh_key()

    def _generate_ssh_key(self):
        if os.path.exists(self.ssh_key_path):
            logger.info(f"SSH key already exists at {self.ssh_key_path}")
            return

        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(self.ssh_key_path)
        os.chmod(self.ssh_key_path, 0o600)
        logger.info(f"Generated SSH key at {self.ssh_key_path}")

    def check_channel_request(self, kind: str, chanid: int) -> int:
        return paramiko.OPEN_SUCCEEDED if kind == 'session' else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username: str) -> str:
        return 'password'

    def check_auth_password(self, username: str, password: str) -> int:
        self.username = username
        self.password = password
        for user in self.allowed_users:
            if username == user.get('username') and password == user.get('password'):
                self.authenticated = True
                logger.info(f"Authentication successful for {username} from {self.client_ip}")
                return paramiko.AUTH_SUCCESSFUL
        logger.warning(f"Authentication failed for {username} from {self.client_ip}")
        return paramiko.AUTH_FAILED

    def check_channel_shell_request(self, channel) -> bool:
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes) -> bool:
        self.user_agent = term  # Capture attacker's terminal type
        return True

    def handle_client(self, client, addr: Tuple[str, int]):
        self.client_ip, self.client_port = addr
        self.session_start = datetime.datetime.now()
        self.session_id = f"{self.client_ip}-{int(self.session_start.timestamp())}"

        try:
            transport = paramiko.Transport(client)
            transport.add_server_key(paramiko.RSAKey(filename=self.ssh_key_path))
            transport.local_version = self.banner
            transport.start_server(server=self)

            chan = transport.accept(20)
            if chan is None:
                logger.warning(f"No channel request from {self.client_ip}")
                return

            self.event.wait(10)
            if not self.event.is_set():
                logger.warning(f"Client {self.client_ip} never requested shell")
                return

            chan.send("Welcome to Ubuntu 20.04.6 LTS\r\n")
            chan.send("$ ")

            self._handle_session(chan)

        except Exception as e:
            logger.error(f"Exception handling client {self.client_ip}: {e}", exc_info=True)

        finally:
            if self.authenticated:
                session_end = datetime.datetime.now()
                log_data = {
                    "ip": self.client_ip,
                    "port": self.client_port,
                    "user_agent": self.user_agent,
                    "username": self.username,
                    "password": self.password,
                    "entered_time": self.session_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "exited_time": session_end.strftime("%Y-%m-%d %H:%M:%S"),
                    "commands": self.executed_commands
                }
                asyncio.run(self._send_log_to_nats(log_data))

    def _handle_session(self, chan):
        buffer = ""
        while True:
            try:
                byte = chan.recv(1)
                if not byte:
                    break

                char = byte.decode('utf-8')
                buffer += char
                chan.send(char)

                if char in ('\r', '\n'):
                    command = buffer.strip()
                    buffer = ""

                    if self.authenticated:
                        self.executed_commands.append(command)

                    if command.lower() in ('exit', 'quit', 'logout'):
                        chan.send("Goodbye.\r\n")
                        chan.close()
                        break

                    response = self._handle_command(command)
                    chan.send(response + "\r\n$ ")
            except Exception as e:
                logger.error(f"Error in command session: {e}", exc_info=True)
                break

    def _handle_command(self, cmd: str) -> str:
        cmd = cmd.strip().lower()
        if cmd == "ls":
            return "bin  boot  dev  etc  home  lib  tmp  usr  var"
        elif cmd == "ps":
            return "  PID TTY          TIME CMD\n 1234 pts/0    00:00:00 bash\n 1235 pts/0    00:00:00 ps"
        elif cmd == "free":
            return "              total        used        free      shared  buff/cache   available\nMem:        1981100      374232      686796        1124      920072     1457332\nSwap:        999420           0      999420"
        else:
            return f"bash: {cmd}: command not found"

    def _sanitize_log_data(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in log_data.items():
            if isinstance(value, bytes):
                sanitized[key] = value.decode('utf-8', errors='replace')
            elif isinstance(value, list):
                sanitized[key] = [v.decode('utf-8', errors='replace') if isinstance(v, bytes) else v for v in value]
            else:
                sanitized[key] = value
        return sanitized

    async def _send_log_to_nats(self, log_data: Dict[str, Any]):
        try:
            publisher = NATSJetstreamPublisher()
            await publisher.connect()
            sanitized_log_data = self._sanitize_log_data(log_data)
            await publisher.publish(sanitized_log_data)
            await publisher.close()
            logger.info(f"Log published to NATS for session {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to publish log to NATS: {e}", exc_info=True)
