from pyftpdlib.handlers import FTPHandler
import os
import time
import datetime
import shutil
import logging

# Setup logging
LOG_DIR = os.path.abspath('./logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'ftp_honeypot.log')

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ftp_honeypot')

# Define the malware directory
MALWARE_DIR = os.path.abspath('./malware')

# Ensure malware directory exists with safe permissions
os.makedirs(MALWARE_DIR, exist_ok=True)
os.chmod(MALWARE_DIR, 0o755)  # Owner rwx, group rx, others rx
logger.info(f"Malware directory set up at: {MALWARE_DIR}")
logger.info(f"Files uploaded by clients will be quarantined here")

# Define the passive port range - must match what's defined in the Honeypot model
PASSIVE_PORT_START = 60000
PASSIVE_PORT_END = 60100  # Same range as in the Honeypot._build_container method

class FTPServer(FTPHandler):
    """
    Enhanced FTP handler for honeypot implementation with comprehensive logging
    """
    
    # Update passive port range to match container configuration
    passive_ports = range(PASSIVE_PORT_START, PASSIVE_PORT_END + 1)
    permit_foreign_addresses = True
    
    def __init__(self, *args, **kwargs):
        self.client_ip = None
        self.client_port = None
        self.client_info = None
        self.username = None
        self.password = None
        self.session_start = None
        self.session_id = None
        FTPHandler.__init__(self, *args, **kwargs)
        
    def on_connect(self):
        """Log when a client connects to the server"""
        self.client_ip = self.remote_ip
        self.client_port = self.remote_port
        self.session_start = time.time()
        self.session_id = f"{self.client_ip}:{self.client_port}-{int(self.session_start)}"
        
        logger.info(f"New connection established")
        logger.info(f"Client IP: {self.client_ip}")
        logger.info(f"Client Port: {self.client_port}")
        logger.info(f"Session Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Session ID: {self.session_id}")
        
        # Get client machine info from FTP client banner if available
        self.client_info = self._get_client_info()
        if self.client_info:
            logger.info(f"Client Machine: {self.client_info}")
            
        super().on_connect()

    def on_disconnect(self):
        """Log when a client disconnects from the server"""
        if hasattr(self, 'session_start') and self.session_start:
            session_duration = time.time() - self.session_start
            logger.info(f"Client disconnected: {self.client_ip}:{self.client_port}")
            logger.info(f"Session Duration: {session_duration:.2f} seconds")
            logger.info(f"Session Ended: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        super().on_disconnect()
        
    def on_login(self, username):
        """Log successful logins to the server"""
        logger.info(f"Successfully authenticated")
        logger.info(f"Username: {self.username}")
        logger.info(f"Password: {self.password}")
        logger.info(f"Client: {self.client_ip}:{self.client_port}")
        super().on_login(username)
        
    def on_login_failed(self, username, password):
        """Log failed login attempts"""
        logger.info(f"Failed login attempt")
        logger.info(f"Username: {username}")
        logger.info(f"Password: {password}")
        logger.info(f"Client: {self.client_ip}:{self.client_port}")
        super().on_login_failed(username, password)
        
    def on_file_sent(self, file):
        """Log when a file is downloaded by the client"""
        logger.info(f"File downloaded: {os.path.basename(file)}")
        logger.info(f"By: {self.username} from {self.client_ip}:{self.client_port}")
        logger.info(f"Full path: {file}")
        super().on_file_sent(file)

    def on_file_received(self, file):
        """Log when a file is uploaded by the client and move it to malware dir with safe permissions"""
        logger.info(f"File uploaded: {os.path.basename(file)}")
        logger.info(f"By: {self.username} from {self.client_ip}:{self.client_port}")
        logger.info(f"Full path: {file}")
        try:
            # Make sure the malware directory exists
            if not os.path.exists(MALWARE_DIR):
                os.makedirs(MALWARE_DIR, exist_ok=True)
                os.chmod(MALWARE_DIR, 0o755)
            
            # Move file to malware directory
            dest_path = os.path.join(MALWARE_DIR, os.path.basename(file))
            if os.path.exists(dest_path):
                # Add timestamp to filename if it already exists
                filename, ext = os.path.splitext(os.path.basename(file))
                timestamp = int(time.time())
                new_filename = f"{filename}_{timestamp}{ext}"
                dest_path = os.path.join(MALWARE_DIR, new_filename)
            
            shutil.move(file, dest_path)
            # Set file permissions: read-only, not executable
            os.chmod(dest_path, 0o444)  # Owner/group/other: read only
            logger.info(f"File securely moved to: {dest_path}")
            logger.info(f"Permissions set to read-only (not executable)")
        except Exception as e:
            logger.error(f"Error moving file to malware directory: {e}")
        
        super().on_file_received(file)
        
    def on_incomplete_file_sent(self, file):
        """Log when a file download is incomplete"""
        logger.warning(f"Incomplete file download: {os.path.basename(file)}")
        logger.warning(f"By: {self.username} from {self.client_ip}:{self.client_port}")
        super().on_incomplete_file_sent(file)

    def on_incomplete_file_received(self, file):
        """Log and remove incomplete file uploads"""
        logger.warning(f"Incomplete file upload: {os.path.basename(file)}")
        logger.warning(f"By: {self.username} from {self.client_ip}:{self.client_port}")
        logger.warning(f"Removing partial file")
        try:
            os.remove(file)
            logger.info(f"Partial file removed: {file}")
        except Exception as e:
            logger.error(f"Error removing partial file: {e}")
        super().on_incomplete_file_received(file)
        
    def on_enter_passive(self):
        """Log passive mode entry"""
        logger.info(f"Client {self.client_ip}:{self.client_port} entered passive mode")
        super().on_enter_passive()
        
    def on_directory_listed(self, path):
        """Log directory listings"""
        logger.info(f"Directory listed: {path}")
        logger.info(f"By: {self.username} from {self.client_ip}:{self.client_port}")
        super().on_directory_listed(path)
        
    def _get_client_info(self):
        """Extract client software information from the FTP client banner"""
        if hasattr(self, 'banner') and self.banner:
            return self.banner.strip()
        return "Unknown"
        
    def process_command(self, cmd, *args, **kwargs):
        """Log all FTP commands received from clients"""
        logger.info(f"Command: {cmd}")
        if args:
            logger.info(f"Args: {' '.join(args)}")
        logger.info(f"From: {self.client_ip}:{self.client_port}")
        return super().process_command(cmd, *args, **kwargs)