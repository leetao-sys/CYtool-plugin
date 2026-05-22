from __future__ import annotations

from app.db.repository import PluginRepository
from app.plugins.errors import PluginError
from app.plugins.runtime import PluginBackendRuntime

from .errors import plugin_error_payload, plugin_error_to_http_status

from pydantic import BaseModel


class BackendCallModel(BaseModel):
    payload: dict[str, object] = {}


def create_plugin_runtime_router(repository: PluginRepository, runtime: PluginBackendRuntime):
    from fastapi import APIRouter, HTTPException

    router = APIRouter(prefix="/runtime/plugins", tags=["plugin-runtime"])

    @router.post("/{plugin_id}/backend/{action}")
    def call_backend(plugin_id: str, action: str, request: BackendCallModel) -> dict[str, object]:
        record = repository.get(plugin_id)
        if record is None or record.status != "enabled":
            raise HTTPException(status_code=404, detail="plugin not found")
        try:
            return {"success": True, "result": runtime.call(record, action, request.payload)}
        except PluginError as exc:
            raise HTTPException(
                status_code=plugin_error_to_http_status(exc),
                detail=plugin_error_payload(exc),
            ) from exc

    return router
