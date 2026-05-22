from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from app.core.paths import RuntimePaths
from app.db.repository import PluginRepository
from app.plugins.lifecycle import PluginLifecycleService
from app.plugins.package import PluginPackageValidator
from app.plugins.runtime import PluginBackendLoader


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PLUGIN_IDS = {
    "encoding_converter": "encoding-converter",
    "json_formatter": "json-formatter",
    "remote_command": "remote-command",
    "time_converter": "time-converter",
}


class ReferencePluginTests(unittest.TestCase):
    def package_plugin(self, source: Path, destination: Path) -> Path:
        archive_path = destination / f"{source.name}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in source.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(source).as_posix())
        return archive_path

    def test_reference_plugins_validate_install_and_load_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime_root = root / "runtime"
            package_root = root / "packages"
            package_root.mkdir()
            paths = RuntimePaths.from_project_root(runtime_root)
            repository = PluginRepository(paths.data / "cytool.sqlite3")
            lifecycle = PluginLifecycleService(paths=paths, repository=repository)
            validator = PluginPackageValidator()
            loader = PluginBackendLoader()

            for source_name, plugin_id in REFERENCE_PLUGIN_IDS.items():
                archive_path = self.package_plugin(ROOT / "plugins" / source_name, package_root)
                package = validator.validate(archive_path)
                self.assertEqual(package.manifest.id, plugin_id)

                record = lifecycle.install(archive_path)
                self.assertEqual(record.id, plugin_id)
                self.assertTrue((Path(record.install_path) / record.frontend_entry).exists())

                loaded = loader.load(record)
                self.assertEqual(loaded.plugin_id, plugin_id)
                self.assertEqual(loaded.instance["plugin_id"], plugin_id)

            menus = lifecycle.enabled_menus()
            self.assertEqual(len(menus), 4)
            self.assertEqual([menu["plugin_id"] for menu in menus], [
                "json-formatter",
                "time-converter",
                "encoding-converter",
                "remote-command",
            ])


if __name__ == "__main__":
    unittest.main()

