import yaml
import os
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
    allowed_users = config.get("authentication", {}).get("allowed_users", [])
    banner = config.get("banner", "Apache/2.4.41")
    auth_realm = config.get("auth_realm", "Secure Area")

    
    logger.info("=" * 50)
    logger.info(" HTTP HONEYPOT SERVER STARTING ".center(48, "="))
    logger.info("=" * 50)

    # Log NATS configuration
    nats_url = os.getenv("NATS_URL")
    nats_stream = os.getenv("NATS_STREAM")
    nats_subject = os.getenv("NATS_SUBJECT")
    logger.info(f"NATS Configuration: URL={nats_url}, Stream={nats_stream}, Subject={nats_subject}")
    logger.info(f"Honeypot type: http")

    def handler(*args, **kwargs):
        HoneypotHTTPRequestHandler(*args, allowed_credentials=allowed_users, banner=banner, auth_realm=auth_realm, **kwargs)

    server = HTTPServer((host, port), handler)
    logger.info(f"Listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        server.server_close()

if __name__ == "__main__":
    main()
