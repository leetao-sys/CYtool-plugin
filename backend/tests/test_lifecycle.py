from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core.paths import RuntimePaths
from app.db.repository import PluginRepository
from app.plugins.errors import PluginConflictError, PluginNotFoundError
from app.plugins.lifecycle import PluginLifecycleService

from helpers import write_plugin_zip


class LifecycleTests(unittest.TestCase):
    def create_service(self, root: Path) -> PluginLifecycleService:
        paths = RuntimePaths.from_project_root(root)
        repository = PluginRepository(paths.data / "cytool.sqlite3")
        return PluginLifecycleService(paths=paths, repository=repository)

    def test_install_enable_disable_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service = self.create_service(root)
            archive = write_plugin_zip(root)

            record = service.install(archive)
            self.assertEqual(record.id, "json-formatter")
            self.assertEqual(record.status, "enabled")
            self.assertTrue(Path(record.install_path).exists())
            self.assertTrue(Path(record.data_path).exists())
            self.assertEqual(len(service.enabled_menus()), 1)

            service.disable("json-formatter")
            self.assertEqual(service.list()[0].status, "disabled")
            self.assertEqual(service.enabled_menus(), [])

            service.enable("json-formatter")
            self.assertEqual(service.list()[0].status, "enabled")

            service.uninstall("json-formatter")
            self.assertEqual(service.list(), [])

    def test_install_rejects_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service = self.create_service(root)
            archive = write_plugin_zip(root)
            service.install(archive)
            with self.assertRaises(PluginConflictError):
                service.install(archive)

    def test_update_requires_existing_plugin_and_newer_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service = self.create_service(root)
            archive_v1 = write_plugin_zip(root, version="1.0.0")
            archive_v2 = write_plugin_zip(root, version="1.1.0")

            with self.assertRaises(PluginNotFoundError):
                service.update(archive_v2)

            service.install(archive_v1)
            updated = service.update(archive_v2)
            self.assertEqual(updated.version, "1.1.0")

            with self.assertRaises(PluginConflictError):
                service.update(archive_v1)


if __name__ == "__main__":
    unittest.main()

