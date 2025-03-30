# Project-H.I.V.E

## Setting Up Podman Socket Service

To ensure the Podman API socket service automatically starts at boot, follow these steps for Linux systems using systemd:

### Create the Systemd User Service

1. Create the systemd user directory (if it doesn't exist):

```bash
mkdir -p ~/.config/systemd/user/
```

2. Create the service file:

```bash
cat > ~/.config/systemd/user/podman-socket.service << EOF
[Unit]
Description=Podman API Service
Documentation=man:podman-system-service(1)

[Service]
Type=simple
ExecStart=/usr/bin/podman system service --time=0 unix:///tmp/podman.sock

[Install]
WantedBy=default.target
EOF
```

3. Enable the service to start at boot:

```bash
systemctl --user enable podman-socket.service
```

4. Start the service immediately:

```bash
systemctl --user start podman-socket.service
```

5. Configure your user account to start services at boot (even when not logged in):

```bash
loginctl enable-linger $USER
```

## Verification

To verify the service is running:

```bash
systemctl --user status podman-socket.service
```

You can also check if Podman can connect to the socket:

```bash
podman info
```

### Troubleshooting

If you encounter issues:

1. Check service logs:
```bash
journalctl --user -u podman-socket.service
```

2. Ensure the socket path exists and is accessible:
```bash
ls -la /tmp/podman.sock
```

3. Restart the service after making any changes:
```bash
systemctl --user restart podman-socket.service
```