import os
import yaml
import logging
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.servers import FTPServer as FTPS
from pyftpdlib.handlers import ThrottledDTPHandler
from FTPServer import FTPServer, logger, PASSIVE_PORT_START, PASSIVE_PORT_END

CONFIG_FILE = "config.yaml"

def load_config():
    """Load configuration from YAML file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {CONFIG_FILE}")
        return config
    except FileNotFoundError:
        logger.warning(f"Configuration file {CONFIG_FILE} not found. Using defaults.")
        # Provide default minimal config if file not found
        return {
            'authentication': {'allowed_users': [{'username': 'guest', 'password': 'guest'}]},
            'ftp': {'banner': '220 FTP Server Ready', 'max_connections': 10}
        }
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file {CONFIG_FILE}: {e}")
        # Exit or return default config on parsing error
        exit(1) # Or return a default config

def setup_authorizer(config):
    """Setup FTP authorizer with users from config"""
    authorizer = DummyAuthorizer()

    # Use a bait directory named "public"
    bait_dir = "./public"

    # Create bait directory if it doesn't exist
    os.makedirs(bait_dir, exist_ok=True)
    logger.info(f"Bait directory set to: {bait_dir}")

    # Add users from the configuration file
    users_added = []
    if 'authentication' in config and 'allowed_users' in config['authentication']:
        for user_info in config['authentication']['allowed_users']:
            username = user_info.get('username')
            password = user_info.get('password')
            if username and password:
                # Permissions: 'e' = change dir, 'l' = list files, 'r' = retrieve file, 'w' = write/store file
                authorizer.add_user(username, password, bait_dir, perm='elrw')
                users_added.append(username)
            else:
                logger.warning(f"Skipping invalid user entry in config: {user_info}")

    if not users_added:
        logger.warning("No valid users found in config. Adding default guest user.")
        authorizer.add_user("guest", "guest", bait_dir, perm='elrw')
        users_added.append("guest")

    logger.info(f"Added honeypot users from config: {', '.join(users_added)}")
    logger.info("User permissions include upload capability - files will be moved to secure malware folder")
    return authorizer

def main():
    """Main function to start the FTP honeypot server"""
    logger.info("=" * 50)
    logger.info(" FTP HONEYPOT SERVER STARTING ".center(48, "="))
    logger.info("=" * 50)

    # Load configuration
    config = load_config()

    # Setup the authorizer with honeypot users from config
    authorizer = setup_authorizer(config)

    # Configure the FTP handler
    handler = FTPServer
    handler.authorizer = authorizer
    # Use banner from config, with a simple default
    handler.banner = config.get('ftp', {}).get('banner', '220 FTP Server Ready')
    # Using the shared constants for passive port range
    handler.passive_ports = range(PASSIVE_PORT_START, PASSIVE_PORT_END + 1)

    # Set up throttled data transfers (using fixed values as per simplified version)
    dtp_handler = ThrottledDTPHandler
    dtp_handler.read_limit = 32768  # Simple fixed limit
    dtp_handler.write_limit = 32768 # Simple fixed limit
    handler.dtp_handler = dtp_handler

    # Create and configure the server with simple settings from config or defaults
    server_address = '0.0.0.0'
    server_port = 21
    max_cons = config.get('ftp', {}).get('max_connections', 10)
    max_cons_per_ip = config.get('ftp', {}).get('max_connections_per_ip', 5)

    # Start the server
    try:
        server = FTPS((server_address, server_port), handler)
        server.max_cons = max_cons
        server.max_cons_per_ip = max_cons_per_ip

        logger.info("FTP Honeypot ready to capture attack attempts")
        logger.info(f"Banner: {handler.banner}")
        logger.info(f"Listening on {server_address}:{server_port}")
        logger.info(f"Maximum connections: {server.max_cons}")
        logger.info(f"Max connections per IP: {server.max_cons_per_ip}")
        logger.info(f"Connection speed limit: {dtp_handler.read_limit / 1024:.1f} KB/s (fixed)")
        logger.info(f"Passive port range: {PASSIVE_PORT_START}-{PASSIVE_PORT_END}")
        logger.info(f"Bait directory: ./public")
        logger.info("Waiting for connections...")

        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("Server shutting down... (Keyboard Interrupt)")

    except PermissionError:
        logger.error(f"Error: Cannot bind to port {server_port}. Permission denied.")
        logger.error("Try running with sudo or use a port > 1024")

    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.error(f"Error: Port {server_port} is already in use.")
            logger.error("Try another port or check if another service is using this port")
        else:
            logger.error(f"OSError: {e}")

    except Exception as e:
        logger.error(f"Error: {e}")

    finally:
        logger.info("FTP Honeypot server stopped.")


if __name__ == "__main__":
    main()