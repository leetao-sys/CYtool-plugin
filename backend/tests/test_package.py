from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.plugins.errors import PackageValidationError
from app.plugins.package import PluginPackageValidator


class PackageTests(unittest.TestCase):
    def write_zip(self, root: Path, files: dict[str, str]) -> Path:
        archive_path = root / "plugin.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return archive_path

    def manifest(self) -> str:
        return json.dumps(
            {
                "id": "json-formatter",
                "name": "JSON Formatter",
                "version": "1.0.0",
                "description": "Format JSON",
                "api_version": "1.0",
                "frontend": {"entry": "frontend/index.html"},
                "backend": {"entry": "backend/plugin.py"},
                "menu": {"title": "JSON"},
                "permissions": [],
            }
        )

    def test_validates_package_and_declared_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_path = self.write_zip(
                root,
                {
                    "plugin.json": self.manifest(),
                    "frontend/index.html": "<h1>JSON</h1>",
                    "backend/plugin.py": "def create_plugin(): pass",
                },
            )
            package = PluginPackageValidator().validate(archive_path)
            self.assertEqual(package.manifest.id, "json-formatter")

    def test_rejects_zip_slip_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_path = self.write_zip(
                root,
                {
                    "plugin.json": self.manifest(),
                    "../evil.txt": "bad",
                    "frontend/index.html": "<h1>JSON</h1>",
                    "backend/plugin.py": "def create_plugin(): pass",
                },
            )
            with self.assertRaises(PackageValidationError):
                PluginPackageValidator().validate(archive_path)

    def test_rejects_missing_frontend_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_path = self.write_zip(
                root,
                {
                    "plugin.json": self.manifest(),
                    "backend/plugin.py": "def create_plugin(): pass",
                },
            )
            with self.assertRaises(PackageValidationError):
                PluginPackageValidator().validate(archive_path)


if __name__ == "__main__":
    unittest.main()

