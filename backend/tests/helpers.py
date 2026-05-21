from __future__ import annotations

import json
import zipfile
from pathlib import Path


def plugin_manifest(plugin_id: str = "json-formatter", version: str = "1.0.0") -> str:
    return json.dumps(
        {
            "id": plugin_id,
            "name": "JSON Formatter",
            "version": version,
            "description": "Format JSON",
            "api_version": "1.0",
            "frontend": {"entry": "frontend/index.html"},
            "backend": {"entry": "backend/plugin.py"},
            "menu": {"title": "JSON", "order": 100},
            "permissions": [],
        }
    )


def write_plugin_zip(
    root: Path,
    *,
    plugin_id: str = "json-formatter",
    version: str = "1.0.0",
) -> Path:
    archive_path = root / f"{plugin_id}-{version}.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("plugin.json", plugin_manifest(plugin_id, version))
        archive.writestr("frontend/index.html", "<h1>JSON</h1>")
        archive.writestr("backend/plugin.py", "def create_plugin(): pass")
    return archive_path

