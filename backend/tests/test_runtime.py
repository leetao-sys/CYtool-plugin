from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.db.repository import PluginRepository
from app.plugins.manifest import PluginManifest
from app.plugins.runtime import PluginBackendLoader, PluginBackendRuntime


class RuntimeTests(unittest.TestCase):
    def test_loads_backend_factory_with_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            install_path = root / "installed"
            data_path = root / "data"
            backend_dir = install_path / "backend"
            backend_dir.mkdir(parents=True)
            data_path.mkdir()
            (backend_dir / "plugin.py").write_text(
                "def create_plugin(context):\n"
                "    return {'plugin_id': context.plugin_id, 'data_path': str(context.data_path)}\n",
                encoding="utf-8",
            )

            repo = PluginRepository(root / "cytool.sqlite3")
            repo.initialize()
            manifest = PluginManifest.from_dict(
                {
                    "id": "runtime-plugin",
                    "name": "Runtime",
                    "version": "1.0.0",
                    "description": "Runtime",
                    "api_version": "1.0",
                    "frontend": {"entry": "frontend/index.html"},
                    "backend": {"entry": "backend/plugin.py"},
                    "menu": {"title": "Runtime"},
                    "permissions": [],
                }
            )
            repo.upsert(
                manifest,
                status="enabled",
                install_path=install_path,
                data_path=data_path,
            )
            record = repo.get("runtime-plugin")

            loaded = PluginBackendLoader().load(record)

            self.assertEqual(loaded.instance["plugin_id"], "runtime-plugin")
            self.assertEqual(loaded.instance["data_path"], str(data_path))

    def test_backend_runtime_calls_handle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            install_path = root / "installed"
            data_path = root / "data"
            backend_dir = install_path / "backend"
            backend_dir.mkdir(parents=True)
            data_path.mkdir()
            (backend_dir / "plugin.py").write_text(
                "class Plugin:\n"
                "    def __init__(self, context): self.context = context\n"
                "    def handle(self, action, payload): return {'action': action, 'payload': payload}\n"
                "def create_plugin(context):\n"
                "    return Plugin(context)\n",
                encoding="utf-8",
            )

            repo = PluginRepository(root / "cytool.sqlite3")
            repo.initialize()
            manifest = PluginManifest.from_dict(
                {
                    "id": "runtime-plugin",
                    "name": "Runtime",
                    "version": "1.0.0",
                    "description": "Runtime",
                    "api_version": "1.0",
                    "frontend": {"entry": "frontend/index.html"},
                    "backend": {"entry": "backend/plugin.py"},
                    "menu": {"title": "Runtime"},
                    "permissions": [],
                }
            )
            repo.upsert(manifest, status="enabled", install_path=install_path, data_path=data_path)
            record = repo.get("runtime-plugin")

            result = PluginBackendRuntime().call(record, "echo", {"value": 1})

            self.assertEqual(result, {"action": "echo", "payload": {"value": 1}})


if __name__ == "__main__":
    unittest.main()
