from __future__ import annotations

import unittest

from app.plugins.errors import ManifestValidationError
from app.plugins.manifest import PluginManifest


class ManifestTests(unittest.TestCase):
    def valid_manifest(self) -> dict[str, object]:
        return {
            "id": "json-formatter",
            "name": "JSON Formatter",
            "version": "1.0.0",
            "description": "Format JSON",
            "api_version": "1.0",
            "frontend": {"entry": "frontend/index.html"},
            "backend": {"entry": "backend/plugin.py", "factory": "create_plugin"},
            "menu": {"title": "JSON"},
            "permissions": ["database:read", "ssh:command"],
        }

    def test_valid_manifest(self) -> None:
        manifest = PluginManifest.from_dict(self.valid_manifest())
        self.assertEqual(manifest.id, "json-formatter")
        self.assertEqual(manifest.version, "1.0.0")
        self.assertEqual(manifest.backend.entry, "backend/plugin.py")
        self.assertEqual(manifest.permissions, ("database:read", "ssh:command"))

    def test_rejects_invalid_plugin_id(self) -> None:
        data = self.valid_manifest()
        data["id"] = "../bad"
        with self.assertRaises(ManifestValidationError):
            PluginManifest.from_dict(data)

    def test_rejects_unknown_permission(self) -> None:
        data = self.valid_manifest()
        data["permissions"] = ["system:root"]
        with self.assertRaises(ManifestValidationError):
            PluginManifest.from_dict(data)

    def test_rejects_unsafe_entry_path(self) -> None:
        data = self.valid_manifest()
        data["frontend"] = {"entry": "../index.html"}
        with self.assertRaises(ManifestValidationError):
            PluginManifest.from_dict(data)


if __name__ == "__main__":
    unittest.main()

