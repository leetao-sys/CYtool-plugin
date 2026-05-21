from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from app.plugins.errors import PluginError
from app.plugins.lifecycle import PluginLifecycleService

from .errors import plugin_error_payload, plugin_error_to_http_status


def create_plugin_admin_router(lifecycle: PluginLifecycleService, temp_dir: Path):
    from fastapi import APIRouter, File, HTTPException, UploadFile

    router = APIRouter(prefix="/plugins", tags=["plugins"])

    @router.get("")
    def list_plugins() -> list[dict[str, object]]:
        return [record.to_dict() for record in lifecycle.list()]

    @router.post("/upload")
    def upload_plugin(file: UploadFile = File(...)) -> dict[str, object]:
        archive_path = _save_upload(file, temp_dir)
        try:
            record = lifecycle.install(archive_path)
            return {"success": True, "plugin": record.to_dict()}
        except PluginError as exc:
            raise _http_error(exc) from exc
        finally:
            archive_path.unlink(missing_ok=True)

    @router.post("/{plugin_id}/update")
    def update_plugin(plugin_id: str, file: UploadFile = File(...)) -> dict[str, object]:
        archive_path = _save_upload(file, temp_dir)
        try:
            package = lifecycle.package_validator.validate(archive_path)
            if package.manifest.id != plugin_id:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": {
                            "code": "PLUGIN_ID_MISMATCH",
                            "message": "uploaded plugin id does not match target plugin id",
                            "detail": {
                                "target": plugin_id,
                                "uploaded": package.manifest.id,
                            },
                        },
                    },
                )
            record = lifecycle.update(archive_path)
            return {"success": True, "plugin": record.to_dict()}
        except PluginError as exc:
            raise _http_error(exc) from exc
        finally:
            archive_path.unlink(missing_ok=True)

    @router.post("/{plugin_id}/enable")
    def enable_plugin(plugin_id: str) -> dict[str, object]:
        try:
            lifecycle.enable(plugin_id)
            return {"success": True}
        except PluginError as exc:
            raise _http_error(exc) from exc

    @router.post("/{plugin_id}/disable")
    def disable_plugin(plugin_id: str) -> dict[str, object]:
        try:
            lifecycle.disable(plugin_id)
            return {"success": True}
        except PluginError as exc:
            raise _http_error(exc) from exc

    @router.delete("/{plugin_id}")
    def uninstall_plugin(plugin_id: str) -> dict[str, object]:
        try:
            lifecycle.uninstall(plugin_id)
            return {"success": True}
        except PluginError as exc:
            raise _http_error(exc) from exc

    return router


def _save_upload(file: object, temp_dir: Path) -> Path:
    temp_dir.mkdir(parents=True, exist_ok=True)
    filename = getattr(file, "filename", None) or "plugin.zip"
    suffix = Path(filename).suffix or ".zip"
    archive_path = temp_dir / f"{uuid4().hex}{suffix}"
    with archive_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)  # type: ignore[attr-defined]
    return archive_path


def _http_error(error: PluginError):
    from fastapi import HTTPException

    return HTTPException(
        status_code=plugin_error_to_http_status(error),
        detail=plugin_error_payload(error),
    )

