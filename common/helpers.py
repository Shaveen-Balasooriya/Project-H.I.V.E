"""
Shared utilities for Project H.I.V.E container management.

This module provides:
• Global settings & logging initialization
• Rich exceptions that wrap low-level subprocess errors
• A singleton PodmanRunner that standardizes command execution
• Network and Image managers for repeatable tasks
• BaseContainerManager for common container lifecycle methods
"""
from __future__ import annotations
import subprocess
import logging
import os
import threading
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

# Logging setup – modules importing this share the same root logger
_log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=_log_level,
    format="[%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger("hive")

class PodmanError(RuntimeError):
    """Generic wrapper for subprocess.CalledProcessError raised by Podman CLI."""
    def __init__(self, cmd: Sequence[str], stderr: str | None = None):
        self.cmd = " ".join(cmd)
        self.stderr = stderr or ""
        self.msg = self._simplify_error_message()
        super().__init__(self.msg)

    def _simplify_error_message(self) -> str:
        """Convert technical Podman error messages to user-friendly ones."""
        raw_error = f"Podman command failed: {self.cmd}\n{self.stderr}"
        logger.debug(raw_error)
        # Container name conflict
        if "creating container storage: the container name" in self.stderr:
            match = re.search(r'the container name "([^"]+)"', self.stderr)
            if match:
                return f"Container {match.group(1)} already exists"
        # General 'already exists' patterns
        if "already exists" in self.stderr.lower():
            for pattern in [r'container ([^ ]+) already exists', r'honeypot ([^ ]+) already exists']:
                match = re.search(pattern, self.stderr, re.IGNORECASE)
                if match:
                    return f"Container {match.group(1)} already exists"
        # Permission and missing container patterns
        patterns = [
            (r'permission denied', 'Permission denied'),
            (r'no such container', 'Container not found'),
            (r'container ([^ ]+) is already running', r'Container \1 is already running'),
            (r'container ([^ ]+) is not running', r'Container \1 is not running'),
        ]
        for pattern, replacement in patterns:
            if re.search(pattern, self.stderr, re.IGNORECASE):
                return re.sub(pattern, replacement, self.stderr, flags=re.IGNORECASE)
        # Fallback for other errors
        if "Error:" in self.stderr:
            parts = self.stderr.split("Error:", 1)
            msg = parts[1].strip()
            return f"Error: {msg[:30]}..." if len(msg) > 30 else f"Error: {msg}"
        return "Command failed"

class ResourceError(RuntimeError):
    """Raised when host resources (disk, ports, permissions) are insufficient."""

@dataclass(frozen=True)
class HiveConfig:
    network_name: str = "hive-net"
    default_labels: dict[str, str] = None
    def __post_init__(self):
        object.__setattr__(self, 'default_labels', {'owner': 'hive'})

CONFIG = HiveConfig()

class _SingletonMeta(type):
    _instances: dict[type, PodmanRunner] = {}
    _lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class PodmanRunner(metaclass=_SingletonMeta):
    """Executes Podman CLI commands with optional output capture & timeout."""
    def run(
        self,
        cmd: List[str],
        *,
        timeout: Optional[float] = None,
        return_output: bool = False,
    ) -> Optional[str]:
        logger.debug(f"[+] Running: {' '.join(cmd)}")
        try:
            if return_output:
                proc = subprocess.run(
                    cmd, check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    text=True, encoding='utf-8', errors='replace'
                )
                return proc.stdout.strip()
            else:
                subprocess.run(cmd, check=True, timeout=timeout)
                return None
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if hasattr(exc, 'stderr') else ''
            raise PodmanError(cmd, stderr) from exc

class NetworkManager:
    """Ensure that the Hive private network exists and provides utilities."""
    def __init__(self, runner: PodmanRunner | None = None):
        self.runner = runner or PodmanRunner()
    def ensure_exists(self, name: str | None = None) -> None:
        name = name or CONFIG.network_name
        if subprocess.run(['podman', 'network', 'exists', name]).returncode == 0:
            logger.debug(f"Network '{name}' already exists")
            return
        self.runner.run(['podman', 'network', 'create', name])
        logger.info(f"[✓] Network '{name}' created")
    def connect(self, container: str, *, alias: str | None = None, name: str | None = None):
        name = name or CONFIG.network_name
        cmd = ['podman', 'network', 'connect'] + (['--alias', alias] if alias else []) + [name, container]
        self.runner.run(cmd)
        logger.info(f"[✓] Connected {container} to network '{name}'")

class ImageManager:
    """Pulls or builds Podman images as necessary."""
    def __init__(self, runner: PodmanRunner | None = None):
        self.runner = runner or PodmanRunner()
    def ensure_pulled(self, image: str) -> None:
        self.runner.run(['podman', 'pull', image])
        logger.info(f"[✓] Image '{image}' present")
    def ensure_built(self, tag: str, dockerfile_dir: Path, dockerfile: str = 'Dockerfile') -> None:
        if subprocess.run(['podman', 'image', 'exists', tag]).returncode == 0:
            logger.debug(f"Image '{tag}' already built")
            return
        self.runner.run(['podman','build','-t',tag,'-f',dockerfile,str(dockerfile_dir)])
        logger.info(f"[✓] Built image '{tag}'")

class BaseContainerManager:
    """Base class providing common container lifecycle methods."""
    name: str = ''
    image: str = ''
    create_args: List[str] = []
    def __init__(self, runner: PodmanRunner | None = None):
        if not self.name or not self.image:
            raise ValueError("Sub-class must define 'name' and 'image'.")
        self.runner = runner or PodmanRunner()
        self.network_mgr = NetworkManager(self.runner)
        self.image_mgr = ImageManager(self.runner)
    def exists(self) -> bool:
        return subprocess.run(['podman','container','exists',self.name]).returncode == 0
    def create(self) -> None:
        if self.exists(): return
        self.pre_create()
        self.runner.run(['podman','create','--name',self.name,*self.create_args,self.image])
        self.post_create()
        logger.info(f"[✓] Container '{self.name}' created")
    def start(self):
        self.runner.run(['podman','start',self.name])
        logger.info(f"[✓] Started '{self.name}'")
    def stop(self):
        self.runner.run(['podman','stop',self.name])
        logger.info(f"[✓] Stopped '{self.name}'")
    def delete(self):
        if not self.exists(): return
        self.runner.run(['podman','rm','-f',self.name])
        logger.info(f"[✓] Deleted '{self.name}'")
    def status(self) -> str:
        try:
            return self.runner.run(['podman','inspect','-f','{{.State.Status}}',self.name], return_output=True)
        except PodmanError:
            return 'not found'
    def pre_create(self): pass
    def post_create(self): pass
