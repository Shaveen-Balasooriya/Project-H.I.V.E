import base64
import logging
import os
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

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
    def __init__(self, *args, allowed_credentials=None, server_header="Apache/2.4.41", auth_realm="Secure Area", **kwargs):
        self.allowed_credentials = allowed_credentials or []
        self.server_version = server_header
        self.sys_version = ""
        self.auth_realm = auth_realm
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

    def do_GET(self):
        username, password = self._parse_auth_header()
        self._log_request(username, password)
        if username is None or not self._is_authorized(username, password):
            self._send_unauthorized()
            return

        parsed_path = urlparse(self.path)
        escaped_path = html.escape(parsed_path.path)
        logger.info(f"Authenticated access to path: {escaped_path}")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        response_content = f"<html><body><h1>Accessed {escaped_path}</h1></body></html>"
        self.wfile.write(response_content.encode('utf-8'))

    def do_POST(self):
        username, password = self._parse_auth_header()
        self._log_request(username, password)
        if username is None or not self._is_authorized(username, password):
            self._send_unauthorized()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        escaped_post_data = html.escape(post_data)

        parsed_path = urlparse(self.path)
        escaped_path = html.escape(parsed_path.path)
        logger.info(f"POST Data: {escaped_post_data}")
        logger.info(f"Authenticated POST to path: {escaped_path}")

        self.send_response(200)
        self.end_headers()
        response_content = f"<html><body><h1>POST to {escaped_path} received!</h1></body></html>"
        self.wfile.write(response_content.encode('utf-8'))
