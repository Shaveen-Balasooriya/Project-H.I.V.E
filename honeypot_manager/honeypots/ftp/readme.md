# FTP Honeypot

A simple FTP honeypot implementation using `pyftpdlib` that simulates an FTP server to capture and log connection attempts.

## Features

- Configurable FTP server banner
- Support for both anonymous access and authenticated users
- Automatic directory creation for users
- Configurable connection limits
- Detailed logging of all FTP commands and activities

## Configuration

The configuration is stored in `config.yaml` and includes the following options:

### Server Settings
- `ip_address`: Address to bind the server (default: 0.0.0.0)
- `port`: Port to listen on (default: 21)

### Authentication
- Configure multiple users with username/password combinations
- Anonymous access supported when no users are defined

### FTP Specific Settings
- `banner`: Custom FTP server banner
- `max_connections`: Maximum number of concurrent connections
- `connection_limit`: Bandwidth throttling option
- `anonymous_dir`: Directory for anonymous users
- `user_dir`: Base directory for authenticated users

## Usage

Run the server directly:
```
python main.py
```

Or build and run using the Project H.I.V.E honeypot manager:
```
# The honeypot will be built and deployed via the honeypot manager API
```

## Implementation Details

This FTP honeypot provides a realistic-looking FTP server that:
1. Accepts connections on the configured port
2. Authenticates users based on the configuration
3. Logs all commands and activities
4. Provides a controlled environment for attackers to interact with

## Extending the Honeypot

To turn this basic FTP server into a more sophisticated honeypot:

1. Add custom response handlers to monitor specific commands
2. Implement fake file structures in user directories
3. Add additional logging for forensic analysis
4. Include deliberately vulnerable areas to track exploitation attempts