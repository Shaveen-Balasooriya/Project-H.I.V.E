import os
import socket
import threading
import yaml
import logging
import sys
import signal
from typing import Dict, Any, Optional
from SSHServer import SSHServer, logger


def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_file: Path to the YAML configuration file
        
    Returns:
        Dict containing the configuration values
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ValueError: If the configuration file has invalid YAML
    """
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        logger.info(f"Configuration loaded from {config_file}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file {config_file}: {e}")
        raise ValueError(f"Invalid YAML in configuration file: {e}")


def setup_signal_handlers(server_socket: socket.socket) -> None:
    """
    Set up signal handlers for graceful shutdown.
    
    Args:
        server_socket: The socket to close on shutdown
    """
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        server_socket.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """
    Main function to start the SSH honeypot server.
    """
    logger.info("=" * 50)
    logger.info(" SSH HONEYPOT SERVER STARTING ".center(48, "="))
    logger.info("=" * 50)
    
    # Log NATS configuration 
    nats_url = os.getenv("NATS_URL")
    nats_stream = os.getenv("NATS_STREAM")
    nats_subject = os.getenv("NATS_SUBJECT")
    honeypot_type = os.getenv("HONEYPOT_TYPE", "ssh")
    
    logger.info(f"NATS Configuration: URL={nats_url}, Stream={nats_stream}, Subject={nats_subject}")
    logger.info(f"Honeypot type: {honeypot_type}")
    
    # Use standard SSH port for containerized deployment
    ip_address = "0.0.0.0"
    port = 22  # Changed from 2222 to standard SSH port 22 for containerization

    try:
        # Load configuration
        config = load_config('config.yaml')
        
        # Create server socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind((ip_address, port))
            server.listen(100)  # Allow up to 100 pending connections
            logger.info(f"Server listening on {ip_address}:{port}")
            
            # Set up signal handlers for graceful shutdown
            setup_signal_handlers(server)
            
            # Main server loop
            while True:
                try:
                    client_sock, client_addr = server.accept()
                    logger.info(f"Connection from {client_addr[0]}:{client_addr[1]}")
                    
                    # Create SSH server instance
                    ssh_server = SSHServer(config)
                    
                    # Start a thread to handle this client
                    client_thread = threading.Thread(
                        target=ssh_server.handle_client,
                        args=(client_sock, client_addr),
                        daemon=True  # Set as daemon so it will exit when main thread exits
                    )
                    client_thread.start()
                    
                except (socket.error, OSError) as e:
                    logger.error(f"Socket error accepting connection: {e}")
                    # Continue running to accept next connection
                    continue
                    
        except PermissionError:
            logger.critical(f"Permission error binding to port {port}. This likely requires root privileges.")
            sys.exit(1)
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.critical(f"Port {port} is already in use. Another service may be running on this port.")
            else:
                logger.critical(f"Error binding to {ip_address}:{port} - {e}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
    finally:
        logger.info("SSH honeypot server shutting down")
        try:
            server.close()
        except Exception:
            # Socket might already be closed
            pass
        logger.info("=" * 50)


if __name__ == "__main__":
    main()