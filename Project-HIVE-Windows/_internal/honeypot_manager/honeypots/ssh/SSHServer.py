import os
import datetime
import logging
import paramiko
import threading
import asyncio
import random
import time
import socket
from typing import Dict, Any, Tuple, List, Optional
from NATSJetstreamPublisher import NATSJetstreamPublisher

# Logging Setup - Ensure correct container paths
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
    # Exit command keywords to filter out
    EXIT_COMMANDS = ['exit', 'quit', 'logout']
    
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
        
        # Virtual filesystem and session state
        self.current_dir = "/home/ubuntu"
        self.hostname = "ubuntu-server"
        self.filesystem = self._setup_virtual_filesystem()
        self.command_history = []
        
        self._generate_ssh_key()

    def _setup_virtual_filesystem(self) -> Dict[str, Any]:
        """Create a simple virtual filesystem structure."""
        return {
            "/": {"type": "dir", "content": ["bin", "boot", "dev", "etc", "home", "lib", "media", "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"]},
            "/home": {"type": "dir", "content": ["ubuntu"]},
            "/home/ubuntu": {"type": "dir", "content": [".bashrc", ".profile", ".ssh", "Documents", "Downloads"]},
            "/home/ubuntu/.ssh": {"type": "dir", "content": ["authorized_keys", "id_rsa", "id_rsa.pub", "known_hosts"]},
            "/home/ubuntu/Documents": {"type": "dir", "content": ["notes.txt", "todo.txt"]},
            "/home/ubuntu/Downloads": {"type": "dir", "content": []},
            "/home/ubuntu/notes.txt": {"type": "file", "content": "Remember to update server configs\nBackup database on Friday\n"},
            "/home/ubuntu/todo.txt": {"type": "file", "content": "1. Update packages\n2. Configure firewall\n3. Check logs\n"},
            "/etc": {"type": "dir", "content": ["passwd", "shadow", "hosts", "resolv.conf", "ssh", "crontab"]},
            "/etc/ssh": {"type": "dir", "content": ["sshd_config", "ssh_config"]},
            "/etc/passwd": {"type": "file", "content": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nbin:x:2:2:bin:/bin:/usr/sbin/nologin\nsys:x:3:3:sys:/dev:/usr/sbin/nologin\nsync:x:4:65534:sync:/bin:/bin/sync\ngames:x:5:60:games:/usr/games:/usr/sbin/nologin\nman:x:6:12:man:/var/cache/man:/usr/sbin/nologin\nlp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin\nubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash\n"},
            "/etc/hosts": {"type": "file", "content": "127.0.0.1 localhost\n127.0.1.1 ubuntu-server\n\n# The following lines are desirable for IPv6 capable hosts\n::1     ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\n"}
        }

    def _generate_ssh_key(self):
        need_new_key = True
        
        if os.path.exists(self.ssh_key_path):
            # Check if key file has valid content
            try:
                with open(self.ssh_key_path, 'r') as f:
                    if f.read().strip():
                        # File exists and has content
                        need_new_key = False
                        logger.info(f"SSH key already exists at {self.ssh_key_path}")
                    else:
                        logger.warning(f"SSH key file exists but is empty, regenerating")
            except Exception as e:
                logger.warning(f"Error reading SSH key file: {e}, regenerating")
        
        if need_new_key:
            # Backup any existing file
            if os.path.exists(self.ssh_key_path):
                backup_path = f"{self.ssh_key_path}.bak.{int(datetime.datetime.now().timestamp())}"
                try:
                    os.rename(self.ssh_key_path, backup_path)
                    logger.info(f"Backed up corrupted key file to {backup_path}")
                except Exception as e:
                    logger.warning(f"Failed to back up key file: {e}")
                    try:
                        os.remove(self.ssh_key_path)
                    except:
                        pass
            
            # Generate new key
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

            # Send a realistic SSH banner with login information
            last_login = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 5), 
                                                 hours=random.randint(1, 23), 
                                                 minutes=random.randint(1, 59))).strftime("%a %b %d %H:%M:%S %Y")
            fake_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            
            welcome_banner = (
                f"\r\n"
                f"Welcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.15.0-88-generic x86_64)\r\n"
                f"\r\n"
                f" * Documentation:  https://help.ubuntu.com\r\n"
                f" * Management:     https://landscape.canonical.com\r\n"
                f" * Support:        https://ubuntu.com/advantage\r\n"
                f"\r\n"
                f"  System information as of {datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')}\r\n"
                f"\r\n"
                f"  System load:  0.{random.randint(1, 20)}\r\n"
                f"  Usage of /:   {random.randint(15, 40)}% of {random.randint(50, 500)}GB\r\n"
                f"  Memory usage: {random.randint(15, 40)}%\r\n"
                f"  Swap usage:   {random.randint(0, 5)}%\r\n"
                f"  Processes:    {random.randint(100, 300)}\r\n"
                f"\r\n"
                f"{random.randint(0, 8)} updates can be applied immediately.\r\n"
                f"{random.randint(0, 3)} of these updates are standard security updates.\r\n"
                f"To see these additional updates run: apt list --upgradable\r\n"
                f"\r\n"
                f"Last login: {last_login} from {fake_ip}\r\n"
            )
            
            chan.send(welcome_banner)
            
            self._handle_session(chan)

        except Exception as e:
            logger.error(f"Exception handling client {self.client_ip}: {e}", exc_info=True)

        finally:
            if self.authenticated:
                # Filter out exit commands before sending log
                filtered_commands = self._filter_exit_commands(self.executed_commands)
                
                session_end = datetime.datetime.now()
                log_data = {
                    "honeypot_type": "ssh",
                    "attacker_ip": self.client_ip,
                    "attacker_port": self.client_port,
                    "user-agent": self.user_agent or "",
                    "username": self.username,
                    "password": self.password,
                    "time_of_entry": self.session_start.isoformat() + "Z",
                    "time_of_exit": session_end.isoformat() + "Z",
                    "commands_executed": filtered_commands
                }
                # Restore NATS logging
                asyncio.run(self._send_log_to_nats(log_data))
                
                # Keep local logging as well
                logger.info(f"Session ended for {self.username} from {self.client_ip}")
                logger.info(f"Commands executed: {filtered_commands}")

    def _filter_exit_commands(self, commands: list) -> list:
        """
        Filter out exit commands from the executed commands list
        
        Args:
            commands: List of commands to filter
            
        Returns:
            List of commands with exit commands removed
        """
        return [cmd for cmd in commands if not any(exit_cmd in cmd.lower() for exit_cmd in self.EXIT_COMMANDS)]

    def _handle_session(self, chan):
        """Handle an interactive SSH session."""
        buffer = ""
        # Send the initial prompt with properly formatted hostname and path
        prompt = f"{self.username}@{self.hostname}:{self._get_prompt_path()}$ "
        chan.send(prompt)
        
        while True:
            try:
                # Receive bytes one at a time
                byte = chan.recv(1)
                if not byte:  # Connection closed by client
                    break
                
                # Convert byte to character
                char = byte.decode('utf-8', errors='replace')
                
                # Handle special characters
                if char == '\x7f' or char == '\b':  # Backspace
                    if buffer:
                        buffer = buffer[:-1]
                        chan.send('\b \b')  # Move back, erase, move back
                    continue
                elif char == '\x03':  # Ctrl+C
                    chan.send('^C\r\n')  # Show ^C and go to new line
                    buffer = ""  # Clear buffer
                    chan.send(prompt)  # Show prompt again
                    continue
                elif char == '\x04':  # Ctrl+D (EOF)
                    if not buffer:  # EOF on empty line means exit
                        chan.send("logout\r\n")
                        break
                    continue  # Ignore otherwise
                
                # Regular character - echo it back
                chan.send(char)
                buffer += char
                
                # Handle Enter key
                if char == '\r' or char == '\n':
                    # Make sure we're at the start of a new line
                    chan.send('\r\n')
                    
                    # Extract command and reset buffer
                    command = buffer.strip('\r\n')
                    buffer = ""
                    
                    if command:  # Only process non-empty commands
                        if self.authenticated:
                            self.executed_commands.append(command)
                            self.command_history.append(command)
                        
                        # Handle exit commands
                        if command.lower() in self.EXIT_COMMANDS:
                            chan.send("logout\r\n")
                            time.sleep(0.2)
                            chan.close()
                            break
                        
                        # Add a small delay for realism
                        time.sleep(random.uniform(0.05, 0.2))
                        
                        # Get command response
                        response = self._handle_command(command)
                        
                        # Send the response with proper line endings
                        if response:
                            # Clean up any inconsistent line endings
                            response = response.replace('\r\n', '\n').replace('\r', '\n')
                            
                            # Add proper line endings for the terminal
                            lines = response.split('\n')
                            for i, line in enumerate(lines):
                                if line:  # Skip empty lines
                                    chan.send(line)
                                # Ensure we have a proper line ending after each line
                                if i < len(lines) - 1 or response.endswith('\n'):
                                    chan.send('\r\n')
                                    
                            # Always ensure we end with a line break if we didn't already
                            if not response.endswith('\n'):
                                chan.send('\r\n')
                    
                    # Always send a carriage return + line feed before the prompt
                    # to ensure it starts on a new line, separate from any previous output
                    chan.send(prompt)
            
            except Exception as e:
                logger.error(f"Error in SSH session: {e}", exc_info=True)
                break
        
        # Close the channel when done
        try:
            chan.close()
        except:
            pass

    def _get_prompt_path(self) -> str:
        """Return the path to display in the prompt."""
        if self.current_dir == f"/home/{self.username}":
            return "~"
        elif self.current_dir.startswith(f"/home/{self.username}/"):
            return "~" + self.current_dir[len(f"/home/{self.username}"):]
        return self.current_dir

    def _handle_command(self, cmd: str) -> str:
        """
        Handle a command and return the response. 
        Simplified to support only the most common commands.
        """
        cmd_parts = cmd.strip().split()
        if not cmd_parts:
            return ""
            
        command = cmd_parts[0].lower()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        # Core set of commands
        if command == "ls":
            return self._handle_ls(args)
        elif command == "cd":
            return self._handle_cd(args)
        elif command == "pwd":
            return self.current_dir
        elif command == "cat":
            return self._handle_cat(args)
        elif command == "whoami":
            return self.username
        elif command == "ps":
            return self._handle_ps()
        elif command == "uname":
            return self._handle_uname(args)
        elif command == "date":
            return self._handle_date(args)
        
        # Command not found for any other command
        else:
            return f"bash: {command}: command not found"

    def _handle_ls(self, args: List[str]) -> str:
        """Simple implementation of ls command."""
        target_dir = self.current_dir
        
        # Parse simple flags
        show_hidden = False
        long_format = False
        
        for arg in args:
            if arg.startswith('-'):
                if 'a' in arg:
                    show_hidden = True
                if 'l' in arg:
                    long_format = True
            elif not arg.startswith('-'):
                target_dir = self._resolve_path(arg)
                break
        
        if target_dir not in self.filesystem:
            return f"ls: cannot access '{target_dir}': No such file or directory"
        
        if self.filesystem[target_dir]["type"] != "dir":
            return f"ls: cannot list '{target_dir}': Not a directory"
        
        # Get the contents
        contents = self.filesystem[target_dir]["content"]
        
        # Filter hidden files unless -a is used
        if not show_hidden:
            contents = [item for item in contents if not item.startswith('.')]
            
        # Sort with directories first for nicer display
        dir_contents = []
        file_contents = []
        
        for item in contents:
            path = self._join_path(target_dir, item)
            if path in self.filesystem and self.filesystem[path]["type"] == "dir":
                dir_contents.append(item)
            else:
                file_contents.append(item)
                
        dir_contents.sort()
        file_contents.sort()
        contents = dir_contents + file_contents
        
        if not contents:
            return ""
            
        if long_format:
            # Long format (-l)
            result = [f"total {len(contents)}"]
            date_str = datetime.datetime.now().strftime("%b %d %H:%M")
            
            for item in contents:
                path = self._join_path(target_dir, item)
                if path in self.filesystem and self.filesystem[path]["type"] == "dir":
                    line = f"drwxr-xr-x 2 {self.username} {self.username} 4096 {date_str} {item}"
                else:
                    line = f"-rw-r--r-- 1 {self.username} {self.username} {random.randint(100, 4000)} {date_str} {item}"
                result.append(line)
                
            return "\n".join(result)
        else:
            # Format in columns like real ls
            output = ""
            col_width = max(len(item) for item in contents) + 2
            num_cols = max(1, 80 // col_width)  # Assuming 80 chars terminal width
            
            # Group items into rows for columnar output
            rows = []
            for i in range(0, len(contents), num_cols):
                row = contents[i:i+num_cols]
                rows.append(row)
                
            # Build output with proper spacing
            formatted_rows = []
            for row in rows:
                formatted_row = ""
                for item in row:
                    path = self._join_path(target_dir, item)
                    if path in self.filesystem and self.filesystem[path]["type"] == "dir":
                        formatted_row += f"{item}/".ljust(col_width)
                    else:
                        formatted_row += item.ljust(col_width)
                formatted_rows.append(formatted_row)
                
            return "\n".join(formatted_rows)

    def _handle_cd(self, args: List[str]) -> str:
        """Simple implementation of cd command."""
        if not args:
            self.current_dir = f"/home/{self.username}"
            return ""
        
        target_dir = self._resolve_path(args[0])
        
        if target_dir not in self.filesystem:
            return f"bash: cd: {args[0]}: No such file or directory"
        
        if self.filesystem[target_dir]["type"] != "dir":
            return f"bash: cd: {args[0]}: Not a directory"
        
        self.current_dir = target_dir
        return ""

    def _handle_cat(self, args: List[str]) -> str:
        """Simple implementation of cat command."""
        if not args:
            return ""
        
        filepath = self._resolve_path(args[0])
        
        if filepath not in self.filesystem:
            return f"cat: {args[0]}: No such file or directory"
        
        if self.filesystem[filepath]["type"] == "dir":
            return f"cat: {args[0]}: Is a directory"
        
        return self.filesystem[filepath].get("content", "")

    def _handle_ps(self) -> str:
        """Simple implementation of ps command."""
        header = "  PID TTY          TIME CMD"
        processes = [
            " 1234 pts/0    00:00:00 bash",
            " 1256 pts/0    00:00:00 sshd",
            " 2345 pts/0    00:00:00 ps"
        ]
        return header + "\n" + "\n".join(processes)

    def _handle_uname(self, args: List[str]) -> str:
        """Simple implementation of uname command."""
        if "-a" in args:
            return "Linux ubuntu-server 5.15.0-88-generic #98-Ubuntu SMP Mon Mar 18 14:22:38 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux"
        return "Linux"

    def _handle_date(self, args: List[str]) -> str:
        """Simple implementation of date command."""
        return datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")

    # Path handling utilities
    def _join_path(self, base: str, path: str) -> str:
        """Join two path components."""
        if base.endswith('/'):
            return base + path
        return base + '/' + path
        
    def _dirname(self, path: str) -> str:
        """Get the directory name of a path."""
        if path == '/':
            return '/'
            
        parts = path.rstrip('/').split('/')
        if len(parts) == 2 and parts[0] == '':  # Handle '/directory'
            return '/'
            
        return '/'.join(parts[:-1]) or '/'
        
    def _basename(self, path: str) -> str:
        """Get the base name of a path."""
        return path.rstrip('/').split('/')[-1]
    
    def _resolve_path(self, path: str) -> str:
        """Resolve a path (absolute or relative) to an absolute path."""
        if not path:
            return self.current_dir
            
        # Handle absolute paths
        if path.startswith('/'):
            result = path
        # Handle home directory
        elif path == "~" or path.startswith("~/"):
            if path == "~":
                result = f"/home/{self.username}"
            else:
                result = f"/home/{self.username}/{path[2:]}"
        # Handle parent directory
        elif path == "..":
            result = self._dirname(self.current_dir)
        elif path.startswith("../"):
            parent = self._dirname(self.current_dir)
            result = self._join_path(parent, path[3:])
        # Handle current directory
        elif path == ".":
            result = self.current_dir
        elif path.startswith("./"):
            result = self._join_path(self.current_dir, path[2:])
        # Handle relative paths
        else:
            result = self._join_path(self.current_dir, path)
            
        # Normalize the path
        return self._normalize_path(result)
        
    def _normalize_path(self, path: str) -> str:
        """Normalize a path, resolving . and .. components."""
        components = path.split('/')
        result = []
        
        for component in components:
            if component == '' or component == '.':
                continue
            elif component == '..':
                if result and result[-1] != '':
                    result.pop()
            else:
                result.append(component)
                
        normalized = '/' + '/'.join(result)
        return normalized if normalized != '' else '/'

    def _sanitize_log_data(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize log data before sending to NATS."""
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
        """Send captured data to NATS JetStream."""
        try:
            publisher = NATSJetstreamPublisher()
            await publisher.connect()
            sanitized_log_data = self._sanitize_log_data(log_data)
            await publisher.publish(sanitized_log_data)
            await publisher.close()
            logger.info(f"Log published to NATS for session {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to publish log to NATS: {e}", exc_info=True)
