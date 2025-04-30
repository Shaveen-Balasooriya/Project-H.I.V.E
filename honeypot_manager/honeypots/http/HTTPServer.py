import base64
import logging
import os
import html
import datetime
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from typing import Dict, Any
from NATSJetstreamPublisher import NATSJetstreamPublisher

# Set up logging
LOG_DIR = os.path.abspath('logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'http_honeypot.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("http_honeypot")

class HoneypotHTTPRequestHandler(BaseHTTPRequestHandler):
    # Track client sessions
    active_sessions = {}
    
    def __init__(self, *args, allowed_credentials=None, banner="Apache/2.4.41", auth_realm="Secure Area", **kwargs):
        self.allowed_credentials = allowed_credentials or []
        self.server_version = banner
        self.sys_version = ""
        self.auth_realm = auth_realm
        self.session_start = datetime.datetime.now()
        self.commands_executed = []
        self.authenticated = False
        self.username = None
        self.password = None
        super().__init__(*args, **kwargs)

    def _send_unauthorized(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', f'Basic realm="{html.escape(self.auth_realm)}"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Unauthorized")

    def _parse_auth_header(self):
        auth_header = self.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            encoded_credentials = auth_header.split(' ')[1]
            try:
                decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
                username, password = decoded_credentials.split(':', 1)
                self.username = username
                self.password = password
                return username, password
            except Exception as e:
                logger.error(f"Error decoding credentials: {e}")
        return None, None

    def _is_authorized(self, username, password):
        for cred in self.allowed_credentials:
            if cred['username'] == username and cred['password'] == password:
                return True
        return False

    def _log_request(self, username, password):
        client_ip, client_port = self.client_address
        user_agent = self.headers.get('User-Agent', 'Unknown')
        logger.info(f"Request from {client_ip}:{client_port}")
        logger.info(f"User-Agent: {html.escape(user_agent)}")
        logger.info(f"Credentials - Username: {html.escape(username or '')}, Password: {html.escape(password or '')}")
        logger.info(f"Path: {html.escape(self.path)}")
        logger.info(f"Headers:\n{self.headers}")
        
        # Track this command
        self.commands_executed.append(f"{self.command} {self.path}")

    def _get_session_key(self):
        """Create a unique key for this client session"""
        client_ip, client_port = self.client_address
        return f"{client_ip}:{client_port}"
        
    def _register_session(self):
        """Register or update an authenticated session"""
        if self.authenticated:
            session_key = self._get_session_key()
            user_agent = self.headers.get('User-Agent', 'Unknown')
            # Store session info
            self.active_sessions[session_key] = {
                'ip': self.client_address[0],
                'port': self.client_address[1],
                'username': self.username,
                'password': self.password,
                'user_agent': user_agent,
                'start_time': self.session_start,
                'commands': self.commands_executed,
                'last_activity': datetime.datetime.now()
            }
            logger.info(f"Authenticated session registered/updated for {session_key}")
    
    def _end_session(self):
        """End a session and send data to NATS"""
        session_key = self._get_session_key()
        if session_key in self.active_sessions:
            session_data = self.active_sessions[session_key]
            session_end = datetime.datetime.now()
            
            try:
                # Prepare log data
                log_data = {
                    "honeypot_type": "http",
                    "attacker_ip": session_data['ip'],
                    "attacker_port": session_data['port'],
                    "user-agent": session_data['user_agent'],
                    "username": session_data['username'],
                    "password": session_data['password'],
                    "time_of_entry": session_data['start_time'].isoformat() + "Z",
                    "time_of_exit": session_end.isoformat() + "Z",
                    "commands_executed": session_data['commands']
                }
                
                # Send to NATS
                asyncio.run(self._send_to_nats(log_data))
                logger.info(f"Session data for {session_key} sent to NATS")
                
                # Remove the session
                del self.active_sessions[session_key]
                logger.info(f"Session for {session_key} ended")
            except Exception as e:
                logger.error(f"Error sending session data to NATS: {e}")
    
    async def _send_to_nats(self, log_data: Dict[str, Any]):
        """Send session data to NATS"""
        publisher = NATSJetstreamPublisher()
        await publisher.connect()
        await publisher.publish(log_data)
        await publisher.close()

    def do_GET(self):
        username, password = self._parse_auth_header()
        self._log_request(username, password)
        
        # Handle authorization
        if username is None or not self._is_authorized(username, password):
            self._send_unauthorized()
            return
            
        # User is authenticated
        self.authenticated = True
        self._register_session()

        parsed_path = urlparse(self.path)
        escaped_path = html.escape(parsed_path.path)
        logger.info(f"Authenticated access to path: {escaped_path}")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        response_content = f"<html><body><h1>Accessed {escaped_path}</h1></body></html>"
        self.wfile.write(response_content.encode('utf-8'))
        
        # End the session after GET responses
        self._end_session()

    def do_POST(self):
        username, password = self._parse_auth_header()
        self._log_request(username, password)
        
        # Handle authorization
        if username is None or not self._is_authorized(username, password):
            self._send_unauthorized()
            return
        
        # User is authenticated
        self.authenticated = True
        self._register_session()

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        escaped_post_data = html.escape(post_data)

        parsed_path = urlparse(self.path)
        escaped_path = html.escape(parsed_path.path)
        logger.info(f"POST Data: {escaped_post_data}")
        logger.info(f"Authenticated POST to path: {escaped_path}")

        # Add the POST data as a command
        self.commands_executed.append(f"POST_DATA: {escaped_post_data[:100]}")
        
        self.send_response(200)
        self.end_headers()
        response_content = f"<html><body><h1>POST to {escaped_path} received!</h1></body></html>"
        self.wfile.write(response_content.encode('utf-8'))
        
        # End the session after POST responses
        self._end_session()
