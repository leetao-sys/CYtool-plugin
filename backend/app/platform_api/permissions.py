from __future__ import annotations

from app.db.repository import PluginRepository, PluginRecord

from .errors import PermissionDeniedError, PluginUnavailableError


class PluginPermissionService:
    def __init__(self, repository: PluginRepository) -> None:
        self.repository = repository

    def require(self, plugin_id: str, permission: str) -> PluginRecord:
        record = self.repository.get(plugin_id)
        if record is None:
            raise PluginUnavailableError("plugin is not installed")
        if record.status != "enabled":
            raise PluginUnavailableError("plugin is not enabled")
        if permission not in record.permissions:
            raise PermissionDeniedError(
                "plugin does not declare required platform API permission",
                detail={"plugin_id": plugin_id, "permission": permission},
            )
        return record

