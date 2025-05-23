from __future__ import annotations
import os
import json
import socket
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from common.helpers import CONFIG, PodmanRunner, ImageManager, NetworkManager
from honeypot_manager.util.exceptions import (
    HoneypotActiveConnectionsError,
    HoneypotContainerError,
    HoneypotError,
    HoneypotExistsError,
    HoneypotImageError,
    HoneypotPrivilegedPortError,
    HoneypotTypeNotFoundError,
    HoneypotPortInUseError,
)

logger = logging.getLogger("hive.honeypot")


class HoneypotConfig:
    """
    Load and cache honeypot-type configurations from a YAML file.
    Falls back to defaults if the file is missing or malformed.
    """
    _CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "honeypot_configs.yaml"
    _DEFAULTS: Dict[str, Any] = {
        "ssh": {"ports": {"22/tcp": "honeypot_port"}},
        "ftp": {
            "ports": {"21/tcp": "honeypot_port"},
            "passive_ports": [60000, 60100],
        },
    }
    _cache: Optional[Dict[str, Any]] = None
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

    @classmethod
    def get(cls, t: str) -> Dict[str, Any]:
        cfg = cls.load()
        if t not in cfg:
            raise HoneypotTypeNotFoundError(f"Unknown honeypot type '{t}'")
        return cfg[t] or {}

    @classmethod
    def exists(cls, t: str) -> bool:
        return t in cls.load()

    @classmethod
    def types(cls) -> List[str]:
        return list(cls.load().keys())


class HoneypotManager:
    """
    Manage a single honeypot container via Podman CLI.
    """

    BASE_DIR = Path(__file__).resolve().parent.parent
    NATS_URL = "nats://hive-nats-server:4222"
    NATS_STREAM = "honeypot"
    NATS_SUBJECT = "honeypot.logs"

    def __init__(
        self,
        runner: PodmanRunner | None = None,
        img_mgr: ImageManager | None = None,
        net_mgr: NetworkManager | None = None,
    ):
        self.runner = runner or PodmanRunner()
        self.img_mgr = img_mgr or ImageManager(self.runner)
        self.net_mgr = net_mgr or NetworkManager(self.runner)
        self.reset_metadata()

    def reset_metadata(self) -> None:
        self.id: Optional[str] = None
        self.name: Optional[str] = None
        self.type: Optional[str] = None
        self.port: Optional[int] = None
        self.status: Optional[str] = None
        self.image: Optional[str] = None

    @staticmethod
    def _validate_port(port: int) -> None:
        if not 1 <= port <= 65535:
            raise ValueError(f"Port {port} out of range (1–65535)")
        if port < 1024:
            raise HoneypotPrivilegedPortError(f"Port {port} requires root privileges")

    @staticmethod
    def _format_memory(value: Union[int, str]) -> str:
        if isinstance(value, int):
            return f"{value}m"
        if isinstance(value, str) and value.isdigit():
            return f"{value}m"
        return str(value)

    def update_honeypot_config(
        self,
        honeypot_type: str,
        authentication: Optional[Dict[str, Any]] = None,
        banner: Optional[str] = None,
    ) -> None:
        cfg_path = self.BASE_DIR / "honeypots" / honeypot_type / "config.yaml"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config {cfg_path} not found")
        try:
            cfg = yaml.safe_load(cfg_path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise HoneypotError(f"Invalid YAML in {cfg_path}: {exc}")
        if authentication is not None:
            cfg["authentication"] = authentication
        if banner is not None:
            cfg["banner"] = banner
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False))

    def create_honeypot(
        self,
        *,
        honeypot_type: str,
        honeypot_port: int,
        honeypot_cpu_limit: int = 100_000,
        honeypot_cpu_quota: int = 50_000,
        honeypot_memory_limit: Union[int, str] = "512m",
        honeypot_memory_swap_limit: Union[int, str] = "512m",
        authentication: Optional[Dict[str, Any]] = None,
        banner: Optional[str] = None,
    ) -> None:
        # 1) validations
        if not HoneypotConfig.exists(honeypot_type):
            raise HoneypotTypeNotFoundError(honeypot_type)
        self._validate_port(honeypot_port)
        if self.is_port_in_use(honeypot_port):
            raise HoneypotPortInUseError(f"Port {honeypot_port} is already in use")

        # 2) prepare metadata and network
        self.net_mgr.ensure_exists(CONFIG.network_name)
        self.type = honeypot_type
        self.port = honeypot_port
        self.name = f"hive-{honeypot_type}-{honeypot_port}"
        self.image = f"hive-{honeypot_type}-image"

        # 3) update YAML if needed
        if authentication or banner:
            self.update_honeypot_config(honeypot_type, authentication, banner)

        # 4) build image
        hp_dir = self.BASE_DIR / "honeypots" / honeypot_type
        try:
            self.img_mgr.ensure_built(self.image, hp_dir)
        except Exception as exc:
            raise HoneypotImageError(f"Image build failed: {exc}") from exc

        # 5) assemble CLI args safely
        cfg = HoneypotConfig.get(honeypot_type)
        # guard against None in config
        ports_cfg = cfg.get("ports") or {}
        passive_cfg = cfg.get("passive_ports") or []
        ports: List[str] = []
        for spec in ports_cfg:
            cont = spec.split("/")[0]
            ports.extend(["--publish", f"{self.port}:{cont}"])
        for p in passive_cfg:
            ports.extend(["--publish", f"{p}:{p}"])

        vols = ["--volume", f"{hp_dir}:/app/config:ro"]

        envs = [
            "-e", f"NATS_URL={self.NATS_URL}",
            "-e", f"NATS_STREAM={self.NATS_STREAM}",
            "-e", f"NATS_SUBJECT={self.NATS_SUBJECT}",
            "-e", f"HONEYPOT_TYPE={honeypot_type}",
        ] or []

        cpu = ["--cpu-period", str(honeypot_cpu_limit), "--cpu-quota", str(honeypot_cpu_quota)]
        mem = ["--memory", self._format_memory(honeypot_memory_limit), "--memory-swap", self._format_memory(honeypot_memory_swap_limit)]

        # debug logging
        logger.debug(
            "create_honeypot args -> cpu: %s, mem: %s, envs: %s, ports: %s, vols: %s",
            cpu, mem, envs, ports, vols
        )

        cmd: List[str] = [
            "podman", "create",
            "--restart", "always",
            "--name", self.name,
            "--hostname", self.name,
            "--network", CONFIG.network_name,
            "--label", "service=hive-honeypot-manager",
            f"--label=hive.type={honeypot_type}",
            f"--label=hive.port={honeypot_port}",
        ]
        # extend in steps to avoid any NoneType unpack
        if isinstance(cpu, list): cmd.extend(cpu)
        if isinstance(mem, list): cmd.extend(mem)
        cmd.extend(["--security-opt", "no-new-privileges"])
        if isinstance(envs, list): cmd.extend(envs)
        if isinstance(ports, list): cmd.extend(ports)
        if isinstance(vols, list): cmd.extend(vols)
        cmd.append(self.image)

        try:
            self.runner.run(cmd)
        except Exception as exc:
            msg = str(exc).lower()
            if "already exists" in msg:
                raise HoneypotExistsError(self.name) from exc
            raise HoneypotContainerError(f"Creation failed: {exc}") from exc

        # 6) inspect post-create
        self.get_honeypot_details(self.name)

    def start_honeypot(self) -> None:
        if self.status == "running":
            raise HoneypotContainerError(f"{self.name} already running")
        self._lifecycle("start")

    def stop_honeypot(self) -> None:
        if self._has_active_connections(self.port):
            raise HoneypotActiveConnectionsError(f"{self.name} has active connections")
        self._lifecycle("stop")

    def restart_honeypot(self) -> None:
        if self.status != "running":
            raise HoneypotContainerError(f"Cannot restart '{self.name}' when not running")
        self._lifecycle("restart")

    def delete_honeypot(self) -> None:
        if self.status == "running":
            raise HoneypotContainerError("Stop container before deleting")
        self._lifecycle("rm", extra=["-f"])

    def _lifecycle(self, cmd: str, extra: List[str] = []) -> None:
        try:
            self.runner.run(["podman", cmd, *extra, self.name])
            if cmd != "rm":
                self.get_honeypot_details(self.name)
            else:
                self.reset_metadata()
        except Exception as exc:
            raise HoneypotContainerError(f"{cmd} failed: {exc}") from exc

    def get_honeypot_details(self, identifier: str) -> Optional[HoneypotManager]:
        try:
            out = self.runner.run(
                ["podman", "inspect", identifier, "--format", "json"],
                return_output=True
            )
        except Exception as exc:
            msg = str(exc).lower()
            if "no such" in msg:
                return None
            raise HoneypotContainerError(f"Inspect failed: {exc}") from exc

        try:
            data = json.loads(out)[0]
            self.id = data["Id"]
            self.name = data["Name"].lstrip("/")
            self.status = data["State"]["Status"]
            labels = data["Config"].get("Labels", {}) or {}
            self.type = labels.get("hive.type")
            self.port = int(labels.get("hive.port") or 0)
            self.image = data["Config"].get("Image")
            return self
        except Exception as exc:
            raise HoneypotContainerError(f"Parsing inspect output failed: {exc}") from exc

    def _has_active_connections(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return False
            except OSError:
                return True

    def is_port_in_use(self, port: int) -> bool:
        out = self.runner.run(
            ["podman", "ps", "-a", "--filter", f"label=hive.port={port}", "--format", "json"],
            return_output=True
        ) or "[]"
        if json.loads(out):
            return True
        return self._has_active_connections(port)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "port": self.port,
            "status": self.status,
            "image": self.image,
        }
