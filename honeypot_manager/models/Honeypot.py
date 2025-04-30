from __future__ import annotations

"""Honeypot container orchestration via **Podman CLI**.
This is the *authoritative* implementation used by the controller.
Safety additions:
• Cannot **delete** while container status == *running*.
• Blocks **stop / delete** when the host‑port has *established* inbound
  connections – raises :class:`~honeypot_manager.util.exceptions.HoneypotActiveConnectionsError`.
"""

import json
import logging
import os
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from common.helpers import CONFIG, ImageManager, NetworkManager, PodmanError, PodmanRunner
from honeypot_manager.util.exceptions import (
    HoneypotActiveConnectionsError,
    HoneypotContainerError,
    HoneypotError,
    HoneypotExistsError,
    HoneypotImageError,
    HoneypotPrivilegedPortError,
    HoneypotTypeNotFoundError,
)

logger = logging.getLogger("hive.honeypot")

###############################################################################
# YAML config loader (unchanged)
###############################################################################

class HoneypotConfig:
    _CONFIG_PATH = (
        Path(__file__).resolve().parent.parent / "config" / "honeypot_configs.yaml"
    )
    _DEFAULTS: Dict[str, Any] = {
        "ssh": {"ports": {"22/tcp": "honeypot_port"}},
        "ftp": {
            "ports": {"21/tcp": "honeypot_port"},
            "passive_ports": [60000, 60100],
        },
    }
    _cache: Dict[str, Any] | None = None
    _mtime: float = 0.0

    @classmethod
    def load(cls) -> Dict[str, Any]:
        if not cls._CONFIG_PATH.exists():
            return cls._DEFAULTS
        mtime = cls._CONFIG_PATH.stat().st_mtime
        if cls._cache and mtime <= cls._mtime:
            return cls._cache
        try:
            with cls._CONFIG_PATH.open("r", encoding="utf-8") as fh:
                cls._cache = yaml.safe_load(fh) or {}
                cls._mtime = mtime
        except yaml.YAMLError as exc:
            logger.warning("Malformed YAML – falling back to defaults: %s", exc)
            cls._cache = cls._DEFAULTS
        return cls._cache

    # convenience wrappers ------------------------------------------------
    @classmethod
    def get(cls, t: str) -> Dict[str, Any]:
        cfg = cls.load()
        if t not in cfg:
            raise HoneypotTypeNotFoundError(f"Unknown honeypot type '{t}'")
        return cfg[t]

    @classmethod
    def exists(cls, t: str) -> bool:
        return t in cls.load()

    @classmethod
    def types(cls) -> List[str]:
        return list(cls.load().keys())

###############################################################################
# Runtime manager
###############################################################################

class HoneypotManager:
    """Manage a *single* honeypot container via Podman CLI."""

    BASE_DIR = Path(__file__).resolve().parent.parent

    def __init__(self):
        self.runner = PodmanRunner()
        self.net_mgr = NetworkManager(self.runner)
        self.img_mgr = ImageManager(self.runner)

        # Populated later -------------------------------------------------
        self.honeypot_id: Optional[str] = None
        self.honeypot_name: Optional[str] = None
        self.honeypot_port: Optional[int] = None
        self.honeypot_status: Optional[str] = None
        self.honeypot_type: Optional[str] = None
        self.honeypot_image: Optional[str] = None

    # ------------------------------------------------------------------
    # public API – creation
    # ------------------------------------------------------------------
    def create_honeypot(
        self,
        *,
        honeypot_type: str,
        honeypot_port: int,
        honeypot_cpu_limit: int = 100_000,
        honeypot_cpu_quota: int = 50_000,
        honeypot_memory_limit: str = "512m",
        honeypot_memory_swap_limit: str = "512m",
    ) -> bool:
        """Build image (if needed) & create a *stopped* container."""
        # 1) validations --------------------------------------------------
        if not HoneypotConfig.exists(honeypot_type):
            raise HoneypotTypeNotFoundError(honeypot_type)
        self._validate_port(honeypot_port)
        self.net_mgr.ensure_exists()

        self.honeypot_type = honeypot_type
        self.honeypot_port = honeypot_port
        self.honeypot_name = f"hive-{honeypot_type}-{honeypot_port}"
        self.honeypot_image = f"hive-{honeypot_type}-image"

        honeypot_dir = self.BASE_DIR / "honeypots" / honeypot_type
        if not honeypot_dir.exists():
            raise FileNotFoundError(honeypot_dir)

        # 2) build image if absent ---------------------------------------
        try:
            self.img_mgr.ensure_built(
                tag=self.honeypot_image, dockerfile_dir=honeypot_dir
            )
        except (PodmanError, OSError) as exc:
            raise HoneypotImageError(str(exc)) from exc

        # 3) compose CLI args -------------------------------------------
        cfg = HoneypotConfig.get(honeypot_type)
        ports_cli = self._compose_port_args(cfg)
        vols_cli = self._compose_volume_args(cfg, honeypot_dir)

        create_cmd = [
            "podman",
            "create",
            "--name",
            self.honeypot_name,
            "--hostname",
            self.honeypot_name,
            "--network",
            CONFIG.network_name,
            "--network-alias",
            self.honeypot_name,
            "--label",
            "service=hive-honeypot-manager",
            "--label",
            f"hive.type={honeypot_type}",
            "--label",
            f"hive.port={honeypot_port}",
            "--cpu-period",
            str(honeypot_cpu_limit),
            "--cpu-quota",
            str(honeypot_cpu_quota),
            "--memory",
            honeypot_memory_limit,
            "--memory-swap",
            honeypot_memory_swap_limit,
            "--security-opt",
            "no-new-privileges",
            "-e",
            "NATS_URL=nats://hive-nats-server:4222",
            *ports_cli,
            *vols_cli,
            self.honeypot_image,
        ]

        # 4) run create ---------------------------------------------------
        try:
            self.runner.run(create_cmd)
        except PodmanError as exc:
            if "already exists" in str(exc):
                raise HoneypotExistsError(self.honeypot_name) from exc
            raise HoneypotContainerError(str(exc)) from exc

        # 5) store metadata ---------------------------------------------
        self.honeypot_id = self.runner.run(
            ["podman", "inspect", "-f", "{{.Id}}", self.honeypot_name],
            return_output=True,
        )
        self.honeypot_status = "configured"
        logger.info("[✓] Created honeypot %s", self.honeypot_name)
        return True

    # ------------------------------------------------------------------
    # public API – lifecycle
    # ------------------------------------------------------------------
    def start_honeypot(self) -> bool:
        if self.honeypot_status == "running":
            raise HoneypotContainerError(f"Honeypot '{self.honeypot_name}' is already running")
        return self._simple_lifecycle("start")

    def stop_honeypot(self) -> bool:
        if self.honeypot_status == "stopped" or self.honeypot_status == "exited":
            raise HoneypotContainerError(f"Honeypot '{self.honeypot_name}' is already stopped")
        return self._simple_lifecycle("stop")

    def restart_honeypot(self) -> bool:
        if self.honeypot_status != "running":
            raise HoneypotContainerError(f"Cannot restart honeypot '{self.honeypot_name}' because it's not running")
        return self._simple_lifecycle("restart")

    def delete_honeypot(self) -> bool:
        if self.honeypot_status == "running":  # guard 1
            raise HoneypotContainerError("Cannot delete a running honeypot – stop it first")
        return self._simple_lifecycle("rm", extra=["-f"])

    # ------------------------------------------------------------------
    # public API – inspect
    # ------------------------------------------------------------------
    def get_honeypot_details(self, identifier: str) -> "HoneypotManager | None":
        try:
            out = self.runner.run(["podman", "inspect", identifier, "--format", "json"], return_output=True)
        except PodmanError as exc:
            error_msg = str(exc).lower()
            if "no such object" in error_msg or "no such container" in error_msg:
                # Instead of raising an error, return None to indicate not found
                logger.info(f"Honeypot '{identifier}' not found")
                return None
            raise HoneypotContainerError(f"Failed to inspect honeypot: {exc}")
        except Exception as exc:
            raise HoneypotContainerError(f"Failed to inspect honeypot: {exc}")
            
        try:
            data = json.loads(out)[0]
            self.honeypot_id = data["Id"]
            self.honeypot_name = data["Name"].lstrip("/")
            self.honeypot_status = data["State"].get("Status")
            labels = data["Config"].get("Labels", {}) or {}
            self.honeypot_type = labels.get("hive.type", "unknown")
            self.honeypot_port = int(labels.get("hive.port", 0))
            self.honeypot_image = data["Config"].get("Image")
            return self
        except (IndexError, KeyError, ValueError) as exc:
            logger.error("Failed to parse container info: %s", exc)
            raise HoneypotContainerError(f"Failed to parse honeypot information: {exc}")

    # ------------------------------------------------------------------
    # utilities
    # ------------------------------------------------------------------
    @staticmethod
    def get_available_honeypot_types() -> List[str]:
        return HoneypotConfig.types()

    # ------------------------ internal helpers ------------------------ #
    @staticmethod
    def _validate_port(port: int):
        if not 1 <= port <= 65535:
            raise ValueError("Port out of range 1‑65535")
        if port < 1024 and os.geteuid() != 0:
            raise HoneypotPrivilegedPortError(port)

    def _compose_port_args(self, cfg: Dict[str, Any]) -> List[str]:
        args: List[str] = []
        mapping = {}
        for container_p, _ in (cfg.get("ports") or {}).items():
            mapping[container_p] = self.honeypot_port
        passive = cfg.get("passive_ports")
        if passive and isinstance(passive, list) and len(passive) == 2:
            start, end = passive
            for p in range(start, end + 1):
                mapping[f"{p}/tcp"] = p
        for c, h in mapping.items():
            args += ["-p", f"{h}:{c}"]
        return args

    def _compose_volume_args(self, cfg: Dict[str, Any], hp_dir: Path) -> List[str]:
        args: List[str] = []
        cfg_path = hp_dir / "config.yaml"
        if cfg_path.exists():
            args += ["-v", f"{cfg_path}:/app/config.yaml:Z,ro"]
        for vol in cfg.get("volumes", []):
            host_dir = hp_dir / vol
            host_dir.mkdir(parents=True, exist_ok=True)
            args += ["-v", f"{host_dir}:/app/{vol}:Z,rw"]
        return args

    # -------- lifecycle backend -------------------------------------- #
    def _port_has_established_connections(self) -> bool:
        """Return True if ESTABLISHED sessions exist on honeypot's host‑port."""
        if not self.honeypot_port:
            return False
        # 1) Is anything listening at all?
        try:
            with socket.create_connection(("127.0.0.1", self.honeypot_port), timeout=0.3):
                pass
        except (ConnectionRefusedError, OSError):
            return False  # nothing bound
        # 2) Check for *established* sessions via `ss`.
        try:
            out = subprocess.check_output(
                ["ss", "-Htan", f"sport = :{self.honeypot_port}"]
            ).decode()
            return any("ESTAB" in line for line in out.splitlines())
        except (subprocess.CalledProcessError, FileNotFoundError):
            # conservative fallback – assume in use
            return True

    def _simple_lifecycle(self, verb: str, *, extra: Optional[List[str]] = None) -> bool:
        if not self.honeypot_name:
            raise HoneypotError("Honeypot details not available - call get_honeypot_details() first")
        
        # Guards ------------------------------------------------------------
        if verb in {"stop", "rm"} and self._port_has_established_connections():
            raise HoneypotActiveConnectionsError(
                f"Port {self.honeypot_port} has active connections - cannot {verb} the honeypot"
            )
            
        cmd = ["podman", verb, self.honeypot_name]
        if extra:
            cmd[2:2] = extra
        try:
            self.runner.run(cmd)
            logger.info("[✓] %s %s", verb.capitalize(), self.honeypot_name)
            
            # Update status after operation
            if verb == "start":
                self.honeypot_status = "running"
            elif verb == "stop":
                self.honeypot_status = "stopped" 
            elif verb == "rm":
                self.honeypot_status = "deleted"
                
            return True
        except PodmanError as exc:
            error_msg = str(exc).lower()
            
            # Specific error messages based on the operation and error
            if "no such container" in error_msg:
                raise HoneypotContainerError(f"Honeypot '{self.honeypot_name}' not found")
            elif "already running" in error_msg:
                raise HoneypotContainerError(f"Honeypot '{self.honeypot_name}' is already running")
            elif "not running" in error_msg and verb == "stop":
                raise HoneypotContainerError(f"Honeypot '{self.honeypot_name}' is not running")
            elif "permission denied" in error_msg:
                raise HoneypotPrivilegedPortError(f"Permission denied when trying to {verb} honeypot")
            else:
                raise HoneypotContainerError(f"Failed to {verb} honeypot '{self.honeypot_name}': {exc}")

    # ------------------------------------------------------------------
    # render for API
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        # Ensure we're not returning a dict with null/None values
        # Only include non-None values or convert None to appropriate defaults
        result = {
            "id": self.honeypot_id or "",
            "name": self.honeypot_name or "",
            "type": self.honeypot_type or "",
            "port": self.honeypot_port or 0,
            "status": self.honeypot_status or "unknown",
            "image": self.honeypot_image or "",
        }
        return result
