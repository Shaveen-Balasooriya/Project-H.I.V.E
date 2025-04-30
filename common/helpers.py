#############################
# Shared utilities for Project H.I.V.E container management
#############################
"""Common helper classes and singletons for Podman‑based managers.

This module provides:
• Global settings & logging initialisation
• Rich exceptions that wrap low‑level subprocess errors
• A singleton ``PodmanRunner`` that standardises command execution
• Small managers (network, image) that encapsulate repeatable tasks
• ``BaseContainerManager`` – a thin base‑class that concrete managers
  (OpenSearchManager, NatsServerManager, LogCollectorManager, etc.)
  can inherit from to avoid code duplication.

All managers should import from ``common.helpers`` instead of invoking
subprocess logic directly.
"""
from __future__ import annotations

import subprocess
import logging
import os
import shutil
import threading
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

###############################################################################
# Logging set‑up – modules that import this will inherit the same root logger
###############################################################################
_log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=_log_level,
    format="[%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger("hive")

###############################################################################
# Exceptions
###############################################################################
class PodmanError(RuntimeError):
    """Generic wrapper for subprocess.CalledProcessError raised by Podman CLI."""

    def __init__(self, cmd: Sequence[str], stderr: str | None = None):
        self.cmd = " ".join(cmd)
        self.stderr = stderr or ""
        
        # Create a more user-friendly error message
        self.msg = self._simplify_error_message()
        super().__init__(self.msg)
        
    def _simplify_error_message(self) -> str:
        """Convert technical Podman error messages to user-friendly ones."""
        # Store the raw message for debugging
        raw_error = f"Podman command failed: {self.cmd}\n{self.stderr}"
        logger.debug(raw_error)
        
        # Check for container storage creation error (name conflict)
        if "creating container storage: the container name" in self.stderr:
            match = re.search(r'the container name "([^"]+)" is already in use', self.stderr)
            if match:
                container_name = match.group(1)
                return f"Container {container_name} already exists"
        
        # Extract container name for existence errors
        if "already exists" in self.stderr.lower():
            # Look for container/honeypot name in error message
            patterns = [
                r'container ([^ ]+) already exists',
                r'honeypot ([^ ]+) already exists',
                r'Error: ([^ ]+) already exists'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, self.stderr, re.IGNORECASE)
                if match:
                    return f"Container {match.group(1)} already exists"
            
            # If no match found, try to extract from command
            match = re.search(r'--name ([^ ]+)', self.cmd)
            if match:
                return f"Container {match.group(1)} already exists"
        
        # Other common error patterns with very concise messages
        patterns = [
            (r'permission denied', 'Permission denied'),
            (r'no such container', 'Container not found'),
            (r'container ([^ ]+) is already running', r'Container \1 is already running'),
            (r'container ([^ ]+) is not running', r'Container \1 is not running')
        ]
        
        for pattern, replacement in patterns:
            match = re.search(pattern, self.stderr.lower())
            if match:
                return re.sub(pattern, replacement, self.stderr, flags=re.IGNORECASE)
        
        # For any other errors, provide a minimal message
        if "Error:" in self.stderr:
            parts = self.stderr.split("Error:", 1)
            error_part = parts[1].strip()
            # If error part is too long, truncate it
            if len(error_part) > 30:
                return f"Error: {error_part[:30]}..."
            return f"Error: {error_part}"
                
        # Fall back to a generic message
        return "Command failed"


class ResourceError(RuntimeError):
    """Raised when host resources (disk, ports, permissions) are insufficient."""


###############################################################################
# Configuration / constants – centralised so they can be imported everywhere
###############################################################################
@dataclass(frozen=True)
class HiveConfig:
    network_name: str = "hive-net"
    default_labels: dict[str, str] = None

    def __post_init__(self):
        # dataclass with mutable default requires manual set in __post_init__
        object.__setattr__(self, "default_labels", {"owner": "hive"})


CONFIG = HiveConfig()

###############################################################################
# Singleton runner
###############################################################################
class _SingletonMeta(type):
    _instances: dict[type, "PodmanRunner"] = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class PodmanRunner(metaclass=_SingletonMeta):
    """Executes Podman CLI commands and provides common options like timeout,
    output capture, and automatic error translation to :class:`PodmanError`."""

    def run(
        self,
        cmd: Sequence[str],
        *,
        capture_output: bool = True,
        text: bool = True,
        check: bool = True,
        timeout: Optional[int] = None,
        return_output: bool = False,
    ) -> str | None:
        logger.debug("Running command: %s", " ".join(map(str, cmd)))
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=text,
                check=check,
                timeout=timeout,
            )
            if return_output:
                return result.stdout.strip()
            return None
        except subprocess.CalledProcessError as e:
            raise PodmanError(cmd, e.stderr) from e
        except FileNotFoundError as e:
            raise ResourceError("'podman' executable not found – is Podman installed?") from e


###############################################################################
# Helper managers
###############################################################################
class NetworkManager:
    """Ensure that the Hive private network exists and provide small utilities."""

    def __init__(self, runner: PodmanRunner | None = None):
        self.runner = runner or PodmanRunner()

    def ensure_exists(self, name: str | None = None) -> None:
        name = name or CONFIG.network_name
        exists_code = subprocess.run(["podman", "network", "exists", name]).returncode
        if exists_code == 0:
            logger.debug("Network '%s' already exists", name)
            return
        self.runner.run(["podman", "network", "create", name])
        logger.info("[✓] Network '%s' created", name)

    def connect(self, container: str, *, alias: str | None = None, name: str | None = None):
        name = name or CONFIG.network_name
        cmd = ["podman", "network", "connect"]
        if alias:
            cmd += ["--alias", alias]
        cmd += [name, container]
        self.runner.run(cmd)
        logger.info("[✓] Connected %s to network '%s'", container, name)


class ImageManager:
    """Pulls or builds images as necessary."""

    def __init__(self, runner: PodmanRunner | None = None):
        self.runner = runner or PodmanRunner()

    def ensure_pulled(self, image: str) -> None:
        self.runner.run(["podman", "pull", image])
        logger.info("[✓] Image '%s' present", image)

    def ensure_built(self, tag: str, dockerfile_dir: Path, dockerfile: str = "Dockerfile") -> None:
        exists_code = subprocess.run(["podman", "image", "exists", tag]).returncode
        if exists_code == 0:
            logger.debug("Image '%s' already built", tag)
            return
        self.runner.run([
            "podman", "build", "-t", tag, "-f", dockerfile, str(dockerfile_dir)
        ])
        logger.info("[✓] Built image '%s'", tag)


###############################################################################
# Base container manager
###############################################################################
class BaseContainerManager:
    """A reusable base‑class that factors out 90 % of container orchestration code."""

    #: Must be overridden by subclasses
    name: str = ""
    image: str = ""
    create_args: List[str] = []  # extra args for "podman create"

    def __init__(self, runner: PodmanRunner | None = None):
        if not self.name or not self.image:
            raise ValueError("Sub‑class must define 'name' and 'image'.")
        self.runner = runner or PodmanRunner()
        self.network_mgr = NetworkManager(self.runner)
        self.image_mgr = ImageManager(self.runner)

    # ---------------------------------------------------------------------
    # Lifecycle helpers
    # ---------------------------------------------------------------------
    def exists(self) -> bool:
        return subprocess.run(["podman", "container", "exists", self.name]).returncode == 0

    def create(self) -> None:
        if self.exists():
            logger.info("[✓] Container '%s' already exists", self.name)
            return
        self.pre_create()
        self.runner.run([
            "podman", "create", "--name", self.name, *self.create_args, self.image
        ])
        self.post_create()
        logger.info("[✓] Container '%s' created", self.name)

    def start(self):
        self.runner.run(["podman", "start", self.name])
        logger.info("[✓] Started '%s'", self.name)

    def stop(self):
        self.runner.run(["podman", "stop", self.name])
        logger.info("[✓] Stopped '%s'", self.name)

    def delete(self):
        if not self.exists():
            logger.info("[i] Container '%s' not found – nothing to delete", self.name)
            return
        self.runner.run(["podman", "rm", "-f", self.name])
        logger.info("[✓] Deleted '%s'", self.name)

    def status(self) -> str:
        try:
            return self.runner.run(
                ["podman", "inspect", "-f", "{{.State.Status}}", self.name],
                return_output=True,
            )
        except PodmanError:
            return "not found"

    # ------------------------------------------------------------------
    # Hooks for subclasses
    # ------------------------------------------------------------------
    def pre_create(self):
        """Optional hook executed *before* 'podman create'."""
        pass

    def post_create(self):
        """Optional hook executed *after* 'podman create'."""
        pass
