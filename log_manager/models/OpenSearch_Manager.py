from __future__ import annotations
from pathlib import Path
from typing   import Final
import shutil, subprocess, time, base64, json

from common.helpers import (
    BaseContainerManager, PodmanRunner, ImageManager,
    ResourceError, CONFIG, logger,
)

class OpenSearchManager(BaseContainerManager):
    name  = "hive-opensearch-node"
    image = "docker.io/opensearchproject/opensearch:latest"

    _POD        : Final = "hive-opensearch-pod"
    _VOLUME     : Final = "hive-opensearch-data"
    _DASH_NAME  : Final = "hive-opensearch-dash"
    _DASH_IMAGE : Final = "docker.io/opensearchproject/opensearch-dashboards:latest"
    _MIN_DISK_GB: Final = 8
    _BOOT_WAIT  : Final = 15        # seconds to wait before dashboard start

    # ────────────────────────────────────────────────────────────────────
    def __init__(self, admin_password: str, runner: PodmanRunner | None = None):
        self.admin_password = admin_password

        self.create_args = [
            "--pod", self._POD,
            "--volume", f"{self._VOLUME}:/usr/share/opensearch/data",
            "--env",  "discovery.type=single-node",
            "--env",  f"OPENSEARCH_INITIAL_ADMIN_PASSWORD={admin_password}",
            "--env",  "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g",
            "--memory","2g", "--cpus","2",
            "--security-opt","no-new-privileges",
        ]
        super().__init__(runner)

    # ────────────────────────────────────────────────────────────────────
    def pre_create(self) -> None:
        if not self._has_disk():
            raise ResourceError(f"Need ≥{self._MIN_DISK_GB} GB free for OpenSearch")

        self.network_mgr.ensure_exists()
        ImageManager(self.runner).ensure_pulled(self.image)
        ImageManager(self.runner).ensure_pulled(self._DASH_IMAGE)

        if subprocess.run(["podman","volume","exists",self._VOLUME]).returncode:
            self.runner.run(["podman","volume","create",self._VOLUME])
            logger.info("[✓] Volume '%s' created", self._VOLUME)

        if subprocess.run(["podman","pod","exists",self._POD]).returncode:
            self.runner.run([
                "podman","pod","create","--name",self._POD,
                "--network",CONFIG.network_name,
                "-p","5601:5601",
            ])
            logger.info("[✓] Pod '%s' created", self._POD)

    def post_create(self) -> None:
        if subprocess.run(["podman","container","exists",self._DASH_NAME]).returncode==0:
            return
        self.runner.run([
            "podman","create","--name",self._DASH_NAME,"--pod",self._POD,
            "--env","OPENSEARCH_HOSTS=https://localhost:9200",
            "--memory","1g","--cpus","1","--security-opt","no-new-privileges",
            self._DASH_IMAGE,
        ])
        logger.info("[✓] Dashboard container '%s' created", self._DASH_NAME)

    # ────────────────────────────────────────────────────────────────────
    def start(self):
        super().start()                       # start node
        logger.info("[~] Sleeping %s s for OpenSearch bootstrap", self._BOOT_WAIT)
        time.sleep(self._BOOT_WAIT)
        self.runner.run(["podman","start",self._DASH_NAME])
        logger.info("[✓] Dashboard started")

    def stop(self):
        self.runner.run(["podman","stop",self._DASH_NAME])
        super().stop()

    def delete(self):
        # Try to stop the dashboard if it's running
        try:
            result = self.runner.run(
                ["podman", "inspect", "-f", "{{.State.Status}}", self._DASH_NAME],
                capture_output=True
            )
            if result.stdout.strip() == "running":
                self.runner.run(["podman", "stop", self._DASH_NAME])
                logger.info("[✓] Dashboard container '%s' stopped", self._DASH_NAME)
        except Exception:
            logger.warning("[!] Could not inspect or stop dashboard – continuing deletion")

        # Try to remove the dashboard
        try:
            self.runner.run(["podman", "rm", "-f", self._DASH_NAME])
            logger.info("[✓] Dashboard container '%s' deleted", self._DASH_NAME)
        except Exception:
            logger.warning("[!] Failed to remove dashboard container – it may not exist")

        # Then delete the main OpenSearch node
        super().delete()


    def dashboard_status(self) -> str:
        try:
            state = self.runner.run(
                ["podman", "inspect", "-f", "{{.State.Status}}", self._DASH_NAME],
                return_output=True
            ).strip()
            return state if state else "not found"
        except Exception as e:
            logger.warning("[!] Dashboard status check failed: %s", e)
            return "not found"



    

    # ────────────────────────────────────────────────────────────────────
    def _has_disk(self) -> bool:
        candidates = [
            Path.home()/".local/share/containers/storage/volumes",
            Path("/var/lib/containers/storage/volumes"),
            Path.cwd(),
        ]
        for p in candidates:
            try:
                if p.exists() and shutil.disk_usage(p).free/1024**3 >= self._MIN_DISK_GB:
                    return True
            except (PermissionError,OSError):
                continue
        raise ResourceError("Cannot read any Podman storage path to check free space")
