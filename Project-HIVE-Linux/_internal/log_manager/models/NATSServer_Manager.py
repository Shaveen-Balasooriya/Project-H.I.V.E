# log_manager/models/NATSServer_Manager.py
from __future__ import annotations

"""
NATS JetStream container manager (sub-process flavour).

Fixes:
• image name is passed only once
• explicit 'nats-server --js -m 8222' command stops the entrypoint
  from mis-parsing the image string
• container starts inside the hive-net bridge with a DNS alias
"""

from typing import List

from common.helpers import (
    BaseContainerManager,
    PodmanRunner,
    CONFIG,
    logger,
)


class NatsServerManager(BaseContainerManager):
    # identifiers -----------------------------------------------------------------
    name:  str = "hive-nats-server"
    image: str = "docker.io/library/nats:latest"

    _ALIAS = "hive-nats-server"            # DNS name other containers will use

    # ----------------------------------------------------------------------------- 
    def __init__(self, runner: PodmanRunner | None = None):
        # Flags appearing **before** the image in `podman create`
        self._pre_flags: List[str] = [
            "--hostname", self.name,
            "--network",  CONFIG.network_name,
            "--label",    "owner=hive",
            "--label",    f"hive.type={self.name}",
            "--restart",  "always",
            "--security-opt", "no-new-privileges",
        ]
        super().__init__(runner)

    # ----------------------------------------------------------------------------- 
    # BaseContainerManager interface
    # ----------------------------------------------------------------------------- 
    @property
    def create_args(self) -> List[str]:  # type: ignore[override]
        return [
            *self._pre_flags,
            "--js", "-m", "8222",
        ]

    def create(self) -> None:
        """Create container with image before JS flags for proper Podman parsing."""
        if self.exists():
            logger.info("[✓] Container '%s' already exists", self.name)
            return
        self.pre_create()
        # Image must come before JS flags to avoid Podman treating them as unknown options
        self.runner.run([
            "podman", "create",
            "--name", self.name,
            *self._pre_flags,
            self.image,
            "--js", "-m", "8222",
        ])
        self.post_create()
        logger.info("[✓] Container '%s' created", self.name)

    def pre_create(self):
        """Pull image and make sure *hive-net* exists."""
        self.network_mgr.ensure_exists()
        self.image_mgr.ensure_pulled(self.image)

    def post_create(self):
        """Connect an alias to simplify service discovery."""
        self.network_mgr.connect(self.name, alias=self._ALIAS)
        logger.info("[✓] NATS connected to '%s' with alias '%s'",
                    CONFIG.network_name, self._ALIAS)
