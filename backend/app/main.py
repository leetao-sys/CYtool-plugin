from __future__ import annotations

from pathlib import Path

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover - lets core tests run before deps are installed.
    FastAPI = None  # type: ignore[assignment]

from app.core.paths import RuntimePaths
from app.db.repository import PluginRepository


def create_app():
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install project dependencies first.")

    project_root = Path(__file__).resolve().parents[2]
    paths = RuntimePaths.from_project_root(project_root)
    paths.ensure()
    repository = PluginRepository(paths.data / "cytool.sqlite3")
    repository.initialize()

    app = FastAPI(title="CYtool Plugin", version="0.1.0")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/admin/plugins")
    def list_plugins() -> list[dict[str, object]]:
        return [record.__dict__ for record in repository.list()]

    return app


app = create_app() if FastAPI is not None else None

