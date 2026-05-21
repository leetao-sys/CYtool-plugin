from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.db.repository import PluginRepository
from app.plugins.manifest import PluginManifest


class RepositoryTests(unittest.TestCase):
    def test_upsert_and_status_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = PluginRepository(root / "cytool.sqlite3")
            repo.initialize()
            manifest = PluginManifest.from_dict(
                {
                    "id": "json-formatter",
                    "name": "JSON Formatter",
                    "version": "1.0.0",
                    "description": "Format JSON",
                    "api_version": "1.0",
                    "frontend": {"entry": "frontend/index.html"},
                    "menu": {"title": "JSON"},
                    "permissions": [],
                }
            )
            repo.upsert(
                manifest,
                status="enabled",
                install_path=root / "installed_plugins" / "json-formatter" / "1.0.0",
                data_path=root / "plugin_data" / "json-formatter",
            )

            record = repo.get("json-formatter")
            self.assertIsNotNone(record)
            self.assertEqual(record.status, "enabled")

            self.assertTrue(repo.set_status("json-formatter", "disabled"))
            self.assertEqual(repo.get("json-formatter").status, "disabled")


if __name__ == "__main__":
    unittest.main()

