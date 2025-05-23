from __future__ import annotations

"""Log‑collector container manager.

This container subscribes to NATS, validates structured honeypot messages and
pushes them to OpenSearch.  We build the image locally because it contains
project‑specific Python code and configuration.
"""

from pathlib import Path

from common.helpers import (
    BaseContainerManager,
    ImageManager,
    NetworkManager,
    PodmanRunner,
    logger,
)

class LogCollectorManager(BaseContainerManager):
    name: str = "hive-log-collector"
    image: str = "hive-log-collector"  # local tag

    def __init__(self, admin_password: str, runner: PodmanRunner | None = None) -> None:
        self.admin_password = admin_password

        project_root = Path(__file__).resolve().parent.parent  # ../log_manager
        self.dockerfile_dir = project_root / "log_collector"

        self.create_args = [
            "--hostname", self.name,
            "--network", "bridge",
            "--env", "NATS_URL=nats://hive-nats-server:4222",
            "--env", "OPENSEARCH_USER=admin",
            "--env", f"OPENSEARCH_PASSWORD={admin_password}",
            "--env", "OPENSEARCH_HOST=https://hive-opensearch-pod:9200",
            "--label", "owner=hive",
            "--label", f"hive.type={self.name}",
            "--restart", "always",
            "--security-opt", "no-new-privileges",
        ]
        super().__init__(runner)

    # ------------------------------------------------------------------
    # hooks
    # ------------------------------------------------------------------
    def pre_create(self):
        self.network_mgr.ensure_exists()
        ImageManager(self.runner).ensure_built(
            tag=self.image,
            dockerfile_dir=self.dockerfile_dir,
            dockerfile="Dockerfile.subscriber",
        )

    def post_create(self):
        self.network_mgr.connect(self.name, alias=self.name)
        logger.debug("Log collector connected to hive-net")
