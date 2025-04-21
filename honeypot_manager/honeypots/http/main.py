import yaml
import sys
from http.server import HTTPServer
from HTTPServer import HoneypotHTTPRequestHandler, logger

def load_config(path="config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    host = "0.0.0.0"
    port = 80
    allowed_users = config.get("allowed_users", [])
    server_header = config.get("server_header", "Apache/2.4.41")
    auth_realm = config.get("auth_realm", "Secure Area")

    
    logger.info("=" * 50)
    logger.info(" HTTP HONEYPOT SERVER STARTING ".center(48, "="))
    logger.info("=" * 50)

    def handler(*args, **kwargs):
        HoneypotHTTPRequestHandler(*args, allowed_credentials=allowed_users, **kwargs)

    server = HTTPServer((host, port), handler)
    logger.info(f"Listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        server.server_close()

if __name__ == "__main__":
    main()
