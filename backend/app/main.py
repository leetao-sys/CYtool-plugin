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


def create_app():
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install project dependencies first.")

    config = AppConfig.from_env()
    project_root = Path(__file__).resolve().parents[2]
    paths = RuntimePaths.from_project_root(project_root)
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

    app.include_router(create_plugin_admin_router(lifecycle, paths.temp), prefix="/api/admin")
    app.include_router(create_platform_router(database, ssh), prefix="/api")

    @app.get("/api/runtime/menus")
    def list_enabled_plugin_menus() -> list[dict[str, object]]:
        return lifecycle.enabled_menus()

    return app


app = create_app() if FastAPI is not None else None
