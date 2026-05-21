from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.db.repository import PluginRepository
from app.platform_api.permissions import PluginPermissionService
from app.platform_api.ssh import (
    BecomeConfig,
    SshBatchCommandRequest,
    SshCommandRequest,
    SshHost,
    SshService,
)
from app.plugins.manifest import PluginManifest


class SshServiceTests(unittest.TestCase):
    def create_service(self, root: Path) -> SshService:
        repo = PluginRepository(root / "cytool.sqlite3")
        repo.initialize()
        manifest = PluginManifest.from_dict(
            {
                "id": "ssh-plugin",
                "name": "SSH Plugin",
                "version": "1.0.0",
                "description": "SSH",
                "api_version": "1.0",
                "frontend": {"entry": "frontend/index.html"},
                "menu": {"title": "SSH"},
                "permissions": ["ssh:command", "ssh:batch"],
            }
        )
        repo.upsert(
            manifest,
            status="enabled",
            install_path=root / "installed",
            data_path=root / "data",
        )
        return SshService(PluginPermissionService(repo))

    def test_execute_with_su_become(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = self.create_service(Path(temp))
            result = service.execute(
                SshCommandRequest(
                    plugin_id="ssh-plugin",
                    host=SshHost(
                        host="127.0.0.1",
                        username="user",
                        become=BecomeConfig(enabled=True, method="su", target_user="root"),
                    ),
                    command="whoami",
                )
            )
            self.assertIn("[become:su:root]", result["stdout"])

    def test_execute_with_sudo_become(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = self.create_service(Path(temp))
            result = service.execute(
                SshCommandRequest(
                    plugin_id="ssh-plugin",
                    host=SshHost(
                        host="127.0.0.1",
                        username="user",
                        become=BecomeConfig(enabled=True, method="sudo", target_user="root"),
                    ),
                    command="id",
                )
            )
            self.assertIn("[become:sudo:root]", result["stdout"])

    def test_batch_execute(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = self.create_service(Path(temp))
            result = service.batch_execute(
                SshBatchCommandRequest(
                    plugin_id="ssh-plugin",
                    hosts=(
                        SshHost(host="host1", username="user"),
                        SshHost(host="host2", username="user"),
                    ),
                    command="hostname",
                )
            )
            self.assertEqual(len(result["results"]), 2)


if __name__ == "__main__":
    unittest.main()

