from __future__ import annotations


class PlatformApiError(Exception):
    code = "PLATFORM_API_ERROR"

    def __init__(self, message: str, *, detail: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class PermissionDeniedError(PlatformApiError):
    code = "PERMISSION_DENIED"


class PluginUnavailableError(PlatformApiError):
    code = "PLUGIN_UNAVAILABLE"


class DatabaseApiError(PlatformApiError):
    code = "DATABASE_ERROR"


class SshApiError(PlatformApiError):
    code = "SSH_ERROR"

