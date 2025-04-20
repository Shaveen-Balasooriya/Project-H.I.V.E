import os
import datetime
import logging
import paramiko
import threading
import re
import shlex
from typing import List, Dict, Any, Tuple, NamedTuple

# Configure logging with absolute paths to ensure logs go to the volume mount
LOG_DIR = os.path.abspath('/app/logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'ssh_honeypot.log')

# Configure logging with both file and console handlers
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

# Log startup information
logger.info(f"SSH Honeypot logging initialized")
logger.info(f"Logs will be stored at: {LOG_FILE}")


class ParsedCommand(NamedTuple):
    """Represents a parsed command with its arguments."""
    command: str
    args: List[str]
    raw: str
    flags: List[str]


class SSHServer(paramiko.ServerInterface):
    """
    SSH Honeypot server implementation using Paramiko's ServerInterface.
    
    This class provides a simulated SSH server that logs authentication attempts
    and tracks commands executed by attackers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SSH server with the provided configuration.
        
        Args:
            config: Dictionary containing authentication and SSH settings
        """
        self.event = threading.Event()
        self.allowed_users = config.get('authentication', {}).get('allowed_users', [])
        self.ssh_key_path = config.get('ssh', {}).get('key_path', 'ssh_host_rsa_key')
        self.banner = config.get('ssh', {}).get('banner', 'SSH-2.0-OpenSSH_8.2p1')
        
        # Track client information
        self.client_ip = None
        self.session_start = None
        self.session_id = None
        
        # Initialize virtual filesystem state
        self.current_dir = "/home/root"
        
        # Register command handlers
        self.command_handlers = {
            'ls': self._handle_ls,
            'cat': self._handle_cat,
            'cd': self._handle_cd,
            'pwd': self._handle_pwd,
            'whoami': self._handle_whoami,
            'id': self._handle_id,
            'uname': self._handle_uname,
            'ps': self._handle_ps,
            'ifconfig': self._handle_ifconfig,
            'ip': self._handle_ip,
            'netstat': self._handle_netstat,
            'who': self._handle_who,
            'w': self._handle_who,  # Alias for who
            'date': self._handle_date,
            'uptime': self._handle_uptime,
            'df': self._handle_df,
            'free': self._handle_free,
            'grep': self._handle_grep,
            'find': self._handle_find,
            'wget': self._handle_wget,
            'curl': self._handle_curl,
            'clear': self._handle_clear,
            'echo': self._handle_echo,
        }
        
        # Ensure the SSH key exists
        try:
            self._generate_ssh_key()
        except Exception as e:
            logger.error(f"Error generating SSH key: {e}")
    
    def _generate_ssh_key(self) -> None:
        """
        Generate an SSH key if it doesn't already exist.
        
        The key is used for the SSH server's host key authentication.
        """
        if os.path.exists(self.ssh_key_path):
            logger.info(f"SSH key already exists at {self.ssh_key_path}")
            return
        
        try:
            key = paramiko.RSAKey.generate(2048)
            key.write_private_key_file(self.ssh_key_path)
            # Set secure permissions on key file
            os.chmod(self.ssh_key_path, 0o600)
            logger.info(f"Generated new SSH key at {self.ssh_key_path}")
        except Exception as e:
            logger.error(f"Failed to generate SSH key: {e}")
            raise

    def check_channel_request(self, kind: str, chanid: int) -> int:
        """
        Allow only session channels.
        
        Args:
            kind: The type of channel being requested
            chanid: The channel ID
            
        Returns:
            int: Status code indicating if the channel request is accepted
        """
        if kind == 'session':
            logger.info(f"Channel request accepted: {kind}")
            return paramiko.OPEN_SUCCEEDED
        
        logger.warning(f"Channel request rejected: {kind}")
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username: str) -> str:
        """
        Specify that only password authentication is allowed.
        
        Args:
            username: The username being authenticated
            
        Returns:
            str: Authentication method(s) allowed
        """
        logger.info(f"Authentication attempts allowed for user: {username}")
        return 'password'

    def check_auth_password(self, username: str, password: str) -> int:
        """
        Authenticate the user based on predefined credentials.
        
        Args:
            username: The username to authenticate
            password: The password to authenticate
            
        Returns:
            int: Status code indicating authentication result
        """
        log_data = {
            "event": "auth_attempt",
            "username": username,
            "password": password,
            "ip": self.client_ip,
            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"Password authentication attempt: {log_data}")
        
        for user in self.allowed_users:
            if username == user.get('username') and password == user.get('password'):
                logger.info(f"Authentication successful for user {username} from {self.client_ip}")
                return paramiko.AUTH_SUCCESSFUL
        
        logger.warning(f"Authentication failed for user {username} from {self.client_ip}")
        return paramiko.AUTH_FAILED

    def check_channel_shell_request(self, channel) -> bool:
        """
        Handle a request to open a shell on a channel.
        
        Args:
            channel: The channel to open a shell on
            
        Returns:
            bool: True if the shell request is accepted
        """
        logger.info(f"Shell request accepted from {self.client_ip}")
        self.event.set()
        return True

    def check_channel_pty_request(self, 
                                 channel, 
                                 term: str, 
                                 width: int, 
                                 height: int, 
                                 pixelwidth: int, 
                                 pixelheight: int,
                                 modes) -> bool:
        """
        Handle a request to allocate a PTY on a channel.
        
        Args:
            channel: The channel to allocate a PTY on
            term: Terminal type
            width: Terminal width in characters
            height: Terminal height in characters
            pixelwidth: Terminal width in pixels
            pixelheight: Terminal height in pixels
            modes: Terminal modes
            
        Returns:
            bool: True if the PTY request is accepted
        """
        logger.info(f"PTY request accepted: {term} ({width}x{height}) from {self.client_ip}")
        return True

    def handle_client(self, client, addr: Tuple[str, int]) -> None:
        """
        Handle a client connection and process their commands.
        
        Args:
            client: Socket for the client connection
            addr: Client address tuple (ip, port)
        """
        self.client_ip = addr[0]
        client_port = addr[1]
        self.session_start = datetime.datetime.now()
        self.session_id = f"{self.client_ip}-{int(self.session_start.timestamp())}"
        
        logger.info(f"New connection established from: {self.client_ip}:{client_port}")
        logger.info(f"Session ID: {self.session_id}")
        
        transport = None
        try:
            # Initialize SSH transport
            transport = paramiko.Transport(client)
            transport.add_server_key(paramiko.RSAKey(filename=self.ssh_key_path))
            transport.local_version = self.banner  # Set SSH banner

            # Create server instance with same configuration
            server = SSHServer({
                "authentication": {"allowed_users": self.allowed_users},
                "ssh": {"key_path": self.ssh_key_path, "banner": self.banner},
            })
            server.client_ip = self.client_ip
            server.session_start = self.session_start
            server.session_id = self.session_id

            # Start the transport server
            try:
                transport.start_server(server=server)
            except paramiko.SSHException:
                logger.error(f"SSH negotiation failed for {self.client_ip}")
                transport.close()
                return

            # Wait for a client channel
            chan = transport.accept()
            if chan is None:
                logger.warning(f"No channel from {self.client_ip}")
                transport.close()
                return

            # Wait for the shell request
            server.event.wait(timeout=60)  # Add timeout to prevent hanging
            if not server.event.is_set():
                logger.warning(f"Client {self.client_ip} never requested a shell")
                transport.close()
                return

            # Send welcome banner with proper line breaks
            welcome_message = [
                "Welcome to Ubuntu 20.04.4 LTS",
                "* Documentation:  https://help.ubuntu.com",
                "* Management:     https://landscape.canonical.com",
                "* Support:        https://ubuntu.com/advantage",
                "",
                f"Last login: {datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y')} from 192.168.1.100"
            ]
            
            for line in welcome_message:
                chan.send(line + "\r\n")
            chan.send("$ ")  # Initial prompt

            self._handle_command_session(chan)

        except Exception as e:
            logger.error(f"Exception handling connection from {self.client_ip}: {str(e)}")
        finally:
            if transport:
                transport.close()
            session_duration = (datetime.datetime.now() - self.session_start).total_seconds()
            logger.info(f"Connection from {self.client_ip} closed. Session duration: {session_duration:.2f} seconds")

    def _handle_command_session(self, chan) -> None:
        """
        Handle the client's command session.
        
        Args:
            chan: The channel for communicating with the client
        """
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
                chan.send(char)

                # Accumulate input
                buffer += char

                # Check for command completion (Enter key)
                if char == '\r' or char == '\n':
                    command = buffer.strip()
                    buffer = ""  # Reset buffer

                    # Send a newline to move to next line
                    chan.send('\r\n')

                    # Handle exit commands
                    if command.lower() in ["exit", "quit", "logout"]:
                        chan.send("Connection closed.\r\n")
                        chan.close()
                        session_active = False
                        break

                    # Process command
                    logger.info(f"Command received from {self.client_ip}: {command}")
                    response = self.handle_cmd(command)

                    # Send response with proper line breaks
                    if response:
                        lines = response.split('\n')
                        formatted_response = '\r\n'.join(line.strip() for line in lines)
                        chan.send(formatted_response + "\r\n")
                    
                    chan.send("$ ")  # Prompt for next command

            except UnicodeDecodeError:
                # Handle binary data or encoding issues
                logger.warning(f"Received non-UTF8 data from {self.client_ip}")
                continue
            except Exception as e:
                logger.error(f"Error receiving data from {self.client_ip}: {str(e)}")
                break

    def _parse_command_line(self, cmd_line: str) -> ParsedCommand:
        """
        Parse a command line into command and arguments.
        
        Args:
            cmd_line: The command line to parse
            
        Returns:
            ParsedCommand: Named tuple containing the parsed command components
        """
        try:
            parts = shlex.split(cmd_line)
        except ValueError:
            # Handle unclosed quotes or other parsing errors
            parts = cmd_line.split()
        
        if not parts:
            return ParsedCommand(command="", args=[], raw=cmd_line, flags=[])
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Extract flags (args starting with -)
        flags = [arg for arg in args if arg.startswith('-')]
        
        return ParsedCommand(command=command, args=args, raw=cmd_line, flags=flags)

    def handle_cmd(self, cmd: str) -> str:
        """
        Handle commands received from clients.
        
        Args:
            cmd: The command to process
            
        Returns:
            str: Response to send back to the client
        """
        # Sanitize and normalize command
        cmd = cmd.strip()
        
        # Empty command case
        if not cmd:
            return ""
            
        try:
            # Parse the command line
            parsed_cmd = self._parse_command_line(cmd)
            
            # Log the parsed command
            logger.info(f"Command received from {self.client_ip}: {parsed_cmd.raw}")
            
            # Handle pipe commands as separate commands (simplified)
            if '|' in cmd:
                # Just handle the first command for simplicity
                first_cmd = cmd.split('|')[0].strip()
                return f"{self.handle_cmd(first_cmd)}\n(Output piped to next command)"
                
            # Get the appropriate handler or use the unknown command handler
            handler = self.command_handlers.get(parsed_cmd.command, self._handle_unknown)
            
            # Execute the handler with the parsed command
            response = handler(parsed_cmd)
            
            # Log the command and response
            logger.info(f"Command: '{cmd}' from {self.client_ip}, Response length: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing command '{cmd}' from {self.client_ip}: {str(e)}")
            return f"Error: {str(e)}"
    
    # Command handler methods
    def _handle_unknown(self, parsed_cmd: ParsedCommand) -> str:
        """Handle unknown commands."""
        return f"bash: {parsed_cmd.command}: command not found"
    
    def _handle_ls(self, parsed_cmd: ParsedCommand) -> str:
        """Handle ls command with various flags."""
        # Define a simple virtual filesystem based on current directory
        filesystem = {
            "/": ["bin", "boot", "dev", "etc", "home", "lib", "lib64", "media", "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"],
            "/home": ["root", "admin", "user"],
            "/home/root": ["users.txt", ".bashrc", ".profile", ".ssh"],
            "/etc": ["passwd", "shadow", "hosts", "resolv.conf", "ssh", "nginx", "apache2"],
        }
        
        # Get directory to list (default to current)
        target_dir = self.current_dir
        
        # Handle directory arguments
        non_flag_args = [arg for arg in parsed_cmd.args if not arg.startswith('-')]
        if non_flag_args:
            if non_flag_args[0].startswith('/'):
                target_dir = non_flag_args[0]
            else:
                # Simple path joining - not handling .. or complex paths
                target_dir = os.path.join(self.current_dir, non_flag_args[0])
        
        # Get contents or show error if directory doesn't exist
        contents = filesystem.get(target_dir, None)
        if contents is None:
            return f"ls: cannot access '{target_dir}': No such file or directory"
        
        # Format based on flags
        if "-l" in parsed_cmd.flags or "-la" in parsed_cmd.flags or "-al" in parsed_cmd.flags:
            # Long listing format
            lines = ["total 16"]
            lines.append("drwxr-xr-x 2 root root 4096 Apr 15 12:30 .")
            lines.append("drwxr-xr-x 5 root root 4096 Apr 15 12:29 ..")
            
            for item in contents:
                if item.startswith('.') and not ("-a" in parsed_cmd.flags or "-la" in parsed_cmd.flags or "-al" in parsed_cmd.flags):
                    continue
                    
                if "." in item:  # Simple way to detect files
                    lines.append(f"-rw-r--r-- 1 root root  220 Apr 15 12:28 {item}")
                else:
                    lines.append(f"drwxr-xr-x 2 root root 4096 Apr 15 12:30 {item}")
            return "\n".join(lines)
        else:
            # Simple listing
            visible_items = [item for item in contents if not item.startswith('.') or 
                            "-a" in parsed_cmd.flags]
            return "  ".join(visible_items)
    
    def _handle_cat(self, parsed_cmd: ParsedCommand) -> str:
        """Handle cat command."""
        if not parsed_cmd.args:
            return "usage: cat [file]..."
            
        # Virtual file contents
        files = {
            "users.txt": "admin:x:0:0:Admin User:/home/admin:/bin/bash\nroot:x:0:0:root:/root:/bin/bash",
            "/etc/passwd": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nbin:x:2:2:bin:/bin:/usr/sbin/nologin\nsys:x:3:3:sys:/dev:/usr/sbin/nologin\nsync:x:4:65534:sync:/bin:/bin/sync\ngames:x:5:60:games:/usr/games:/usr/sbin/nologin\nman:x:6:12:man:/var/cache/man:/usr/sbin/nologin\nlp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin\nmail:x:8:8:mail:/var/mail:/usr/sbin/nologin\nnews:x:9:9:news:/var/spool/news:/usr/sbin/nologin\nuucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin\nproxy:x:13:13:proxy:/bin:/usr/sbin/nologin\nwww-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\nbackup:x:34:34:backup:/var/backups:/usr/sbin/nologin\nlist:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin\nirc:x:39:39:ircd:/var/run/ircd:/usr/sbin/nologin\ngnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin\nnobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin\nsystemd-network:x:100:102:systemd Network Management,,,:/run/systemd/netif:/usr/sbin/nologin\nsystemd-resolve:x:101:103:systemd Resolver,,,:/run/systemd/resolve:/usr/sbin/nologin\nsystemd-timesync:x:102:104:systemd Time Synchronization,,,:/run/systemd/timesync:/usr/sbin/nologin\nmessagebus:x:103:106::/nonexistent:/usr/sbin/nologin\nsshd:x:104:65534::/run/sshd:/usr/sbin/nologin\nuser:x:1000:1000:Generic User,,,:/home/user:/bin/bash\nadmin:x:1001:1001:Admin User,,,:/home/admin:/bin/bash",
            "/etc/hosts": "127.0.0.1\tlocalhost\n127.0.1.1\thoneypot\n\n# The following lines are desirable for IPv6 capable hosts\n::1     ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters",
            "/etc/resolv.conf": "nameserver 8.8.8.8\nnameserver 8.8.4.4",
        }
        
        filename = parsed_cmd.args[0]
        
        # Handle absolute vs relative paths
        if not filename.startswith('/'):
            filename = os.path.join(self.current_dir, filename)
            # Normalize path a bit
            if filename.endswith('/'):
                filename = filename[:-1]
        
        # Return file contents or error
        if filename in files:
            return files[filename]
        else:
            return f"cat: {parsed_cmd.args[0]}: No such file or directory"
    
    def _handle_cd(self, parsed_cmd: ParsedCommand) -> str:
        """Handle cd command."""
        # Virtual directories
        valid_dirs = ["/", "/home", "/home/root", "/home/admin", "/etc", "/var", "/tmp"]
        
        # Default to home if no args
        if not parsed_cmd.args:
            self.current_dir = "/home/root"
            return ""
            
        target_dir = parsed_cmd.args[0]
        
        # Handle absolute vs relative paths (simple)
        if not target_dir.startswith('/'):
            target_dir = os.path.join(self.current_dir, target_dir)
        
        # Normalize path
        if target_dir.endswith('/') and target_dir != '/':
            target_dir = target_dir[:-1]
        
        # Check if valid and update current dir
        if target_dir in valid_dirs:
            self.current_dir = target_dir
            return ""
        else:
            return f"bash: cd: {parsed_cmd.args[0]}: No such file or directory"
    
    def _handle_pwd(self, parsed_cmd: ParsedCommand) -> str:
        """Handle pwd command."""
        return self.current_dir
    
    def _handle_whoami(self, parsed_cmd: ParsedCommand) -> str:
        """Handle whoami command."""
        return "root"
    
    def _handle_id(self, parsed_cmd: ParsedCommand) -> str:
        """Handle id command."""
        return "uid=0(root) gid=0(root) groups=0(root)"
    
    def _handle_uname(self, parsed_cmd: ParsedCommand) -> str:
        """Handle uname command."""
        if "-a" in parsed_cmd.flags:
            return "Linux honeypot 5.4.0-107-generic #121-Ubuntu SMP Thu Mar 24 16:04:27 UTC 2022 x86_64 x86_64 x86_64 GNU/Linux"
        else:
            return "Linux"
    
    def _handle_ps(self, parsed_cmd: ParsedCommand) -> str:
        """Handle ps command."""
        headers = "  PID TTY          TIME CMD"
        processes = [
            "    1 ?        00:00:02 systemd",
            "    2 ?        00:00:00 kthreadd",
            "    3 ?        00:00:00 rcu_gp",
            "    4 ?        00:00:00 rcu_par_gp",
            "    6 ?        00:00:00 kworker/0:0H-kblockd",
            "    9 ?        00:00:00 mm_percpu_wq",
            "   10 ?        00:00:00 ksoftirqd/0",
            "   11 ?        00:00:00 rcu_sched",
            "   12 ?        00:00:00 migration/0",
            "  613 ?        00:00:00 sshd",
            "  742 ?        00:00:00 nginx",
            "  743 ?        00:00:00 nginx",
            " 1287 ?        00:00:00 sshd",
            " 1321 pts/0    00:00:00 bash",
            " 1393 pts/0    00:00:00 ps"
        ]
        
        if "-ef" in parsed_cmd.flags or "-aux" in parsed_cmd.flags:
            # Full process listing
            full_headers = "UID        PID  PPID  C STIME TTY          TIME CMD"
            full_processes = [
                "root         1     0  0 Apr01 ?        00:00:02 /sbin/init",
                "root         2     0  0 Apr01 ?        00:00:00 [kthreadd]",
                "root         3     2  0 Apr01 ?        00:00:00 [rcu_gp]",
                "root         4     2  0 Apr01 ?        00:00:00 [rcu_par_gp]",
                "root         6     2  0 Apr01 ?        00:00:00 [kworker/0:0H-kblockd]",
                "root         9     2  0 Apr01 ?        00:00:00 [mm_percpu_wq]",
                "root        10     2  0 Apr01 ?        00:00:00 [ksoftirqd/0]",
                "root       613     1  0 Apr01 ?        00:00:00 /usr/sbin/sshd -D",
                "root       742     1  0 Apr01 ?        00:00:00 nginx: master process",
                "www-data   743   742  0 Apr01 ?        00:00:00 nginx: worker process",
                "root      1287   613  0 12:30 ?        00:00:00 sshd: root@pts/0",
                "root      1321  1287  0 12:30 pts/0    00:00:00 -bash",
                "root      1393  1321  0 12:32 pts/0    00:00:00 ps -ef"
            ]
            return full_headers + "\n" + "\n".join(full_processes)
        
        return headers + "\n" + "\n".join(processes)
    
    def _handle_ifconfig(self, parsed_cmd: ParsedCommand) -> str:
        """Handle ifconfig command."""
        return """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.10  netmask 255.255.255.0  broadcast 192.168.1.255
        inet6 fe80::215:5dff:fe00:101  prefixlen 64  scopeid 0x20<link>
        ether 00:15:5d:00:01:01  txqueuelen 1000  (Ethernet)
        RX packets 38246  bytes 5810012 (5.8 MB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 12485  bytes 1863185 (1.8 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 2520  bytes 136800 (136.8 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 2520  bytes 136800 (136.8 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0"""
    
    def _handle_ip(self, parsed_cmd: ParsedCommand) -> str:
        """Handle ip command."""
        if len(parsed_cmd.args) >= 1 and parsed_cmd.args[0] == "addr":
            return """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:15:5d:00:01:01 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.10/24 brd 192.168.1.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::215:5dff:fe00:101/64 scope link 
       valid_lft forever preferred_lft forever"""
        else:
            return "Usage: ip [ OPTIONS ] OBJECT { COMMAND | help }\nwhere OBJECT := { link | address | route | rule | neigh }"
    
    def _handle_netstat(self, parsed_cmd: ParsedCommand) -> str:
        """Handle netstat command."""
        if "-tuln" in parsed_cmd.flags or "-tulpn" in parsed_cmd.flags or "-an" in parsed_cmd.flags:
            return """Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      613/sshd
tcp        0      0 127.0.0.1:25            0.0.0.0:*               LISTEN      -
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      742/nginx
tcp6       0      0 :::22                   :::*                    LISTEN      613/sshd
tcp6       0      0 :::80                   :::*                    LISTEN      742/nginx
udp        0      0 0.0.0.0:68              0.0.0.0:*                           -"""
        else:
            return """Active Internet connections (w/o servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 192.168.1.10:22         192.168.1.100:54284     ESTABLISHED"""
    
    def _handle_who(self, parsed_cmd: ParsedCommand) -> str:
        """Handle who/w command."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"root     pts/0        {now} ({parsed_cmd.command})"
    
    def _handle_date(self, parsed_cmd: ParsedCommand) -> str:
        """Handle date command."""
        return datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")
    
    def _handle_uptime(self, parsed_cmd: ParsedCommand) -> str:
        """Handle uptime command."""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        return f" {current_time} up 14 days,  3:25,  1 user,  load average: 0.08, 0.03, 0.01"
    
    def _handle_df(self, parsed_cmd: ParsedCommand) -> str:
        """Handle df command."""
        if "-h" in parsed_cmd.flags:
            return """Filesystem      Size  Used Avail Use% Mounted on
udev            916M     0  916M   0% /dev
tmpfs           192M  1.1M  191M   1% /run
/dev/sda1        29G   10G   18G  36% /
tmpfs           957M     0  957M   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           957M     0  957M   0% /sys/fs/cgroup
/dev/sda15      124M   12M  113M  10% /boot/efi
tmpfs           192M     0  192M   0% /run/user/0"""
        else:
            return """Filesystem     1K-blocks    Used Available Use% Mounted on
udev              937340       0    937340   0% /dev
tmpfs             196224    1124    195100   1% /run
/dev/sda1       30309800 10598668  18118220  37% /
tmpfs             981100       0    981100   0% /dev/shm
tmpfs               5120       0      5120   0% /run/lock
tmpfs             981100       0    981100   0% /sys/fs/cgroup
/dev/sda15        126576   11704    114872  10% /boot/efi
tmpfs             196220       0    196220   0% /run/user/0"""
    
    def _handle_free(self, parsed_cmd: ParsedCommand) -> str:
        """Handle free command."""
        if "-h" in parsed_cmd.flags or "-m" in parsed_cmd.flags:
            return """              total        used        free      shared  buff/cache   available
Mem:           1.9Gi       365Mi       671Mi       1.1Mi       868Mi       1.4Gi
Swap:          975Mi          0B       975Mi"""
        else:
            return """              total        used        free      shared  buff/cache   available
Mem:        1981100      374232      686796        1124      920072     1457332
Swap:        999420           0      999420"""
    
    def _handle_grep(self, parsed_cmd: ParsedCommand) -> str:
        """Handle grep command - simplified."""
        return "(No input provided to grep)"
        
    def _handle_find(self, parsed_cmd: ParsedCommand) -> str:
        """Handle find command - simplified."""
        if len(parsed_cmd.args) < 1:
            return "find: missing path argument"
            
        path = parsed_cmd.args[0]
        
        if path == "/" and len(parsed_cmd.args) >= 3 and parsed_cmd.args[1] == "-name":
            return f"find: Permission denied"
        
        return f"find: '{path}': No such file or directory"
    
    def _handle_wget(self, parsed_cmd: ParsedCommand) -> str:
        """Handle wget command."""
        if not parsed_cmd.args:
            return "wget: missing URL"
        
        url = parsed_cmd.args[0]
        
        return f"""--2022-04-15 12:45:23--  {url}
Resolving {url.split('//')[1].split('/')[0]}... 93.184.216.34, 2606:2800:220:1:248:1893:25c8:1946
Connecting to {url.split('//')[1].split('/')[0]}|93.184.216.34|:80... connected.
HTTP request sent, awaiting response... 200 OK
Length: 1256 (1.2K) [text/html]
Saving to: 'index.html'

index.html                      100%[=================================================>]   1.23K  --.-KB/s    in 0s      

2022-04-15 12:45:24 (8.12 MB/s) - 'index.html' saved [1256/1256]"""
    
    def _handle_curl(self, parsed_cmd: ParsedCommand) -> str:
        """Handle curl command."""
        if not parsed_cmd.args:
            return "curl: try 'curl --help' or 'curl --manual' for more information"
        
        url = parsed_cmd.args[0]
        
        return f"""  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  1256  100  1256    0     0  12563      0 --:--:-- --:--:-- --:--:-- 12807
<!DOCTYPE html>
<html>
<head>
<title>Example Domain</title>
</head>
<body>
<h1>Example Domain</h1>
<p>This domain is for use in illustrative examples in documents.</p>
</body>
</html>"""
    
    def _handle_clear(self, parsed_cmd: ParsedCommand) -> str:
        """Handle clear command."""
        return ""  # Just clear the screen
    
    def _handle_echo(self, parsed_cmd: ParsedCommand) -> str:
        """Handle echo command."""
        return " ".join(parsed_cmd.args)