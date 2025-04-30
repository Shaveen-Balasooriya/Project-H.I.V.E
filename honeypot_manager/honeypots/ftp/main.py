import os
import yaml
import random
import datetime
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.servers import FTPServer as FTPS
from pyftpdlib.handlers import ThrottledDTPHandler
from FTPServer import FTPServer, logger, PASSIVE_PORT_START, PASSIVE_PORT_END

CONFIG_FILE = "config.yaml"

def create_dummy_files(directory):
    """Create realistic-looking dummy files in the specified directory"""
    # Check if directory already has files (but create dummy files anyway)
    existing_files = os.listdir(directory)
    if existing_files:
        logger.info(f"Bait directory already contains {len(existing_files)} files, adding dummy files anyway")
    
    dummy_files = [
        {
            "name": "backup.zip",
            "content": b"PK\x03\x04\x14\x00\x00\x00\x08\x00\xFDCEVeO\x7F\x93\x12\x00\x00\x00\x1A\x00\x00\x00\x0C\x00\x00\x00passwords.txt",
            "type": "binary"
        },
        {
            "name": "readme.txt",
            "content": "This directory contains important backup files and documentation.\nPlease do not modify or delete any files without authorization.",
            "type": "text"
        },
        {
            "name": "config.ini", 
            "content": "[database]\nhost=192.168.1.100\nuser=admin\npassword=db@dm1n\n\n[api]\nkey=38a4b7c9d1e2f0\nsecret=39dj48dls2j",
            "type": "text"
        },
        {
            "name": "access_log.csv",
            "content": "timestamp,user,ip,action\n" + "\n".join([
                f"{(datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30), hours=random.randint(1, 23))).strftime('%Y-%m-%d %H:%M:%S')},admin,192.168.1.{random.randint(2, 254)},login" 
                for _ in range(5)
            ]),
            "type": "text"
        },
        {
            "name": "server_notes.txt",
            "content": "TODO:\n- Update firewall rules\n- Change default credentials on routers\n- Check backup integrity\n- Upgrade database to latest version",
            "type": "text"
        },
        {
            "name": "users.db",
            "content": b"SQLite format 3" + b"\x00" * 20 + b"CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT)",
            "type": "binary"
        }
    ]
    
    # Write files to the directory
    for file_info in dummy_files:
        file_path = os.path.join(directory, file_info["name"])
        
        # Skip if file already exists with same name
        if os.path.exists(file_path):
            logger.info(f"Skipping existing file: {file_info['name']}")
            continue
            
        mode = "wb" if file_info["type"] == "binary" else "w"
        
        with open(file_path, mode) as f:
            # Make sure binary content is bytes and text content is str
            if mode == "wb" and isinstance(file_info["content"], str):
                f.write(file_info["content"].encode('utf-8'))
            elif mode == "w" and isinstance(file_info["content"], bytes):
                f.write(file_info["content"].decode('utf-8', errors='replace'))
            else:
                f.write(file_info["content"])
        
        # Set realistic timestamps
        past_time = datetime.datetime.now() - datetime.timedelta(days=random.randint(30, 180))
        mod_time = past_time.timestamp()
        os.utime(file_path, (mod_time, mod_time))
        
        logger.info(f"Created dummy bait file: {file_info['name']}")
    
    logger.info(f"Finished creating dummy bait files")

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
            'banner': '220 FTP Server Ready',
            'ftp': {'max_connections': 10}
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

    # Create dummy files in bait directory if it's empty
    create_dummy_files(bait_dir)

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

    # Log NATS configuration 
    nats_url = os.getenv("NATS_URL")
    nats_stream = os.getenv("NATS_STREAM")
    nats_subject = os.getenv("NATS_SUBJECT")
    logger.info(f"NATS Configuration: URL={nats_url}, Stream={nats_stream}, Subject={nats_subject}")
    logger.info(f"Honeypot type: ftp")

    # Load configuration
    config = load_config()

    # Setup the authorizer with honeypot users from config
    authorizer = setup_authorizer(config)

    # Configure the FTP handler
    handler = FTPServer
    handler.authorizer = authorizer
    # Use banner from config, with a simple default
    handler.banner = config.get('banner', '220 FTP Server Ready')
    # Using the shared constants for passive port range
    handler.passive_ports = range(PASSIVE_PORT_START, PASSIVE_PORT_END + 1)

    # Set up throttled data transfers
    dtp_handler = ThrottledDTPHandler
    dtp_handler.read_limit = config.get('ftp', {}).get('connection_limit', 32768)
    dtp_handler.write_limit = config.get('ftp', {}).get('connection_limit', 32768)
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
        logger.info(f"Connection speed limit: {dtp_handler.read_limit / 1024:.1f} KB/s")
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