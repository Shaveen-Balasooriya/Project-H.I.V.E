from __future__ import annotations
"""High-level orchestration of all log-manager services."""

from typing import Dict, List, Optional
import time

from common.helpers import logger
from log_manager.models.OpenSearch_Manager import OpenSearchManager
from log_manager.models.NATSServer_Manager import NatsServerManager
from log_manager.models.Log_Collector_Manager import LogCollectorManager

class ServiceOrchestrator:
    """Aggregate operations across the three container managers."""
    def __init__(self, admin_password: Optional[str] = None) -> None:
        admin_password = admin_password or "ChangeMe!"
        self.opensearch = OpenSearchManager(admin_password)
        self.nats       = NatsServerManager()
        self.collector  = LogCollectorManager(admin_password)
        self._all       = [self.opensearch, self.nats, self.collector]

    def _exists_map(self) -> Dict[str, bool]:
        return {m.name: m.exists() for m in self._all}

    def _status_map(self) -> Dict[str, str]:
        return {m.name: m.status() for m in self._all}

    def _running_map(self) -> Dict[str, bool]:
        return {m.name: m.status() == "running" for m in self._all}

    def create_all(self) -> None:
        for m in self._all:
            m.create()

    def start_all(self) -> None:
        if self.opensearch.status() != "running":
            self.opensearch.start()
        if self.nats.status() != "running":
            self.nats.start()
        time.sleep(5)
        if self.collector.status() != "running":
            self.collector.start()

    def stop_all(self) -> None:
        for m in reversed(self._all):
            if m.status() == "running":
                m.stop()

    def delete_all(self) -> None:
        for m in reversed(self._all):
            m.delete()

    def restart_all(self) -> None:
        for m in reversed(self._all):
            if m.status() == "running":
                m.stop()
        time.sleep(2)
        for m in self._all:
            m.start()

    def any_exists(self) -> bool:
        return any(self._exists_map().values())

    def any_running(self) -> bool:
        return any(self._running_map().values())

    def missing(self) -> List[str]:
        return [n for n, ok in self._exists_map().items() if not ok]

    def not_running(self) -> List[str]:
        return [n for n, run in self._running_map().items() if not run]

    def status_report(self) -> Dict[str, str]:
        report = self._status_map()
        report["hive-opensearch-dash"] = self.opensearch.dashboard_status()
        return report

