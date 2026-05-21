from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from .errors import ManifestValidationError
from .version import Version

PLUGIN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,62}[a-z0-9]$")
SUPPORTED_API_VERSION = "1.0"
KNOWN_PERMISSIONS = {
    "database:read",
    "database:write",
    "ssh:command",
    "ssh:file_transfer",
    "ssh:batch",
}


@dataclass(frozen=True)
class FrontendManifest:
    entry: str


@dataclass(frozen=True)
class BackendManifest:
    entry: str
    factory: str = "create_plugin"


@dataclass(frozen=True)
class MenuManifest:
    title: str
    icon: str | None = None
    order: int = 1000


@dataclass(frozen=True)
class PluginManifest:
    id: str
    name: str
    version: str
    description: str
    api_version: str
    frontend: FrontendManifest
    menu: MenuManifest
    permissions: tuple[str, ...]
    author: str | None = None
    backend: BackendManifest | None = None

    @property
    def parsed_version(self) -> Version:
        return Version.parse(self.version)

    @classmethod
    def from_json(cls, raw: str) -> "PluginManifest":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ManifestValidationError(
                f"plugin.json is not valid JSON: {exc.msg}",
                detail={"line": exc.lineno, "column": exc.colno},
            ) from exc
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginManifest":
        if not isinstance(data, dict):
            raise ManifestValidationError("plugin manifest must be a JSON object")

        plugin_id = _required_string(data, "id")
        if not PLUGIN_ID_RE.match(plugin_id):
            raise ManifestValidationError(
                "plugin id must use lowercase letters, numbers, dots, or hyphens"
            )

        version = _required_string(data, "version")
        try:
            Version.parse(version)
        except ValueError as exc:
            raise ManifestValidationError(str(exc)) from exc

        api_version = _required_string(data, "api_version")
        if api_version != SUPPORTED_API_VERSION:
            raise ManifestValidationError(
                f"unsupported api_version {api_version!r}; expected {SUPPORTED_API_VERSION!r}"
            )

        frontend_data = _required_object(data, "frontend")
        frontend_entry = _safe_relative_path(_required_string(frontend_data, "entry"))

        menu_data = _required_object(data, "menu")
        menu_title = _required_string(menu_data, "title")
        menu_icon = _optional_string(menu_data, "icon")
        menu_order = menu_data.get("order", 1000)
        if not isinstance(menu_order, int):
            raise ManifestValidationError("menu.order must be an integer")

        raw_permissions = data.get("permissions", [])
        if not isinstance(raw_permissions, list) or not all(
            isinstance(item, str) for item in raw_permissions
        ):
            raise ManifestValidationError("permissions must be a string array")
        unknown_permissions = sorted(set(raw_permissions) - KNOWN_PERMISSIONS)
        if unknown_permissions:
            raise ManifestValidationError(
                "manifest declares unknown permissions",
                detail={"permissions": unknown_permissions},
            )

        backend = None
        backend_data = data.get("backend")
        if backend_data is not None:
            if not isinstance(backend_data, dict):
                raise ManifestValidationError("backend must be an object")
            backend_entry = _safe_relative_path(_required_string(backend_data, "entry"))
            if not backend_entry.endswith(".py"):
                raise ManifestValidationError("backend.entry must point to a Python file")
            backend_factory = _optional_string(backend_data, "factory") or "create_plugin"
            if not backend_factory.isidentifier():
                raise ManifestValidationError("backend.factory must be a valid Python identifier")
            backend = BackendManifest(entry=backend_entry, factory=backend_factory)

        return cls(
            id=plugin_id,
            name=_required_string(data, "name"),
            version=version,
            description=_required_string(data, "description"),
            author=_optional_string(data, "author"),
            api_version=api_version,
            frontend=FrontendManifest(entry=frontend_entry),
            backend=backend,
            menu=MenuManifest(title=menu_title, icon=menu_icon, order=menu_order),
            permissions=tuple(sorted(set(raw_permissions))),
        )


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestValidationError(f"{key} is required and must be a non-empty string")
    return value.strip()


def _optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ManifestValidationError(f"{key} must be a string")
    return value.strip() or None


def _required_object(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ManifestValidationError(f"{key} is required and must be an object")
    return value


def _safe_relative_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ManifestValidationError(f"{value!r} is not a safe relative path")
    return path.as_posix()

