from __future__ import annotations

from app.plugins.errors import (
    ManifestValidationError,
    PackageValidationError,
    PluginConflictError,
    PluginError,
    PluginNotFoundError,
)


def plugin_error_to_http_status(error: PluginError) -> int:
    if isinstance(error, PluginNotFoundError):
        return 404
    if isinstance(error, PluginConflictError):
        return 409
    if isinstance(error, (ManifestValidationError, PackageValidationError)):
        return 400
    return 500


def plugin_error_payload(error: PluginError) -> dict[str, object]:
    return {
        "success": False,
        "error": {
            "code": error.code,
            "message": error.message,
            "detail": error.detail,
        },
    }

