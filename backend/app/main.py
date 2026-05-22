from __future__ import annotations

from pathlib import Path

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover - lets core tests run before deps are installed.
    FastAPI = None  # type: ignore[assignment]

from app.core.config import AppConfig
from app.core.paths import RuntimePaths
from app.db.repository import PluginRepository
from app.plugins.lifecycle import PluginLifecycleService
from app.platform_api.database import DatabaseService
from app.platform_api.permissions import PluginPermissionService
from app.platform_api.ssh import FakeSshExecutor, ParamikoSshExecutor, SshService


def create_app(config: AppConfig | None = None, paths: RuntimePaths | None = None):
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install project dependencies first.")

    config = config or AppConfig.from_env()
    project_root = Path(__file__).resolve().parents[2]
    paths = paths or (
        RuntimePaths.from_data_dir(root=project_root, data=config.data_dir)
        if config.data_dir
        else RuntimePaths.from_project_root(project_root)
    )
    paths.ensure()
    repository = PluginRepository(paths.data / "cytool.sqlite3")
    repository.initialize()
    lifecycle = PluginLifecycleService(paths=paths, repository=repository)
    permissions = PluginPermissionService(repository)
    database = DatabaseService(permissions)
    ssh_executor = FakeSshExecutor() if config.ssh_executor == "fake" else ParamikoSshExecutor()
    ssh = SshService(permissions, executor=ssh_executor)

    app = FastAPI(title="CYtool Plugin", version="0.1.0")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    from app.api.platform import create_platform_router
    from app.api.plugin_admin import create_plugin_admin_router
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    app.include_router(create_plugin_admin_router(lifecycle, paths.temp), prefix="/api/admin")
    app.include_router(create_platform_router(database, ssh), prefix="/api")

    @app.get("/api/runtime/menus")
    def list_enabled_plugin_menus() -> list[dict[str, object]]:
        return lifecycle.enabled_menus()

    @app.get("/plugins/{plugin_id}/index.html")
    def plugin_index(plugin_id: str):
        return _plugin_file(plugin_id, None)

    @app.get("/plugins/{plugin_id}/{asset_path:path}")
    def plugin_asset(plugin_id: str, asset_path: str):
        return _plugin_file(plugin_id, asset_path)

    def _plugin_file(plugin_id: str, asset_path: str | None):
        record = repository.get(plugin_id)
        if record is None or record.status != "enabled":
            raise HTTPException(status_code=404, detail="plugin not found")
        relative_path = asset_path or record.frontend_entry
        if ".." in Path(relative_path).parts:
            raise HTTPException(status_code=400, detail="unsafe plugin asset path")
        file_path = Path(record.install_path) / relative_path
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="plugin asset not found")
        return FileResponse(file_path)

    return app


app = create_app() if FastAPI is not None else None
