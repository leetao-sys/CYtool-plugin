from __future__ import annotations


class PluginError(Exception):
    code = "PLUGIN_ERROR"

    def __init__(self, message: str, *, detail: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class ManifestValidationError(PluginError):
    code = "MANIFEST_INVALID"


class PackageValidationError(PluginError):
    code = "PACKAGE_INVALID"


class PluginConflictError(PluginError):
    code = "PLUGIN_CONFLICT"


class PluginNotFoundError(PluginError):
    code = "PLUGIN_NOT_FOUND"

