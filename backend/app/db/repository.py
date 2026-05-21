from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from app.plugins.manifest import PluginManifest


@dataclass(frozen=True)
class PluginRecord:
    id: str
    name: str
    version: str
    description: str
    status: str
    api_version: str
    permissions: tuple[str, ...]
    menu_title: str
    menu_icon: str | None
    menu_order: int
    frontend_entry: str
    backend_entry: str | None
    backend_factory: str | None
    install_path: str
    data_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "status": self.status,
            "api_version": self.api_version,
            "permissions": list(self.permissions),
            "menu": {
                "title": self.menu_title,
                "icon": self.menu_icon,
                "order": self.menu_order,
            },
            "frontend_entry": self.frontend_entry,
            "backend_entry": self.backend_entry,
            "backend_factory": self.backend_factory,
            "install_path": self.install_path,
            "data_path": self.data_path,
        }

    def to_menu_dict(self) -> dict[str, object]:
        return {
            "plugin_id": self.id,
            "title": self.menu_title,
            "icon": self.menu_icon,
            "order": self.menu_order,
            "route": f"/plugins/{self.id}",
            "frontend_url": f"/plugins/{self.id}/index.html",
        }


class PluginRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists plugins (
                    id text primary key,
                    name text not null,
                    version text not null,
                    description text not null,
                    status text not null,
                    api_version text not null,
                    permissions_json text not null,
                    menu_title text not null default '',
                    menu_icon text,
                    menu_order integer not null default 1000,
                    frontend_entry text not null default '',
                    backend_entry text,
                    backend_factory text,
                    install_path text not null,
                    data_path text not null,
                    created_at text not null default current_timestamp,
                    updated_at text not null default current_timestamp
                )
                """
            )
            self._ensure_plugin_columns(conn)
            conn.execute(
                """
                create table if not exists plugin_operation_logs (
                    id integer primary key autoincrement,
                    plugin_id text,
                    operation text not null,
                    status text not null,
                    message text not null,
                    detail_json text not null default '{}',
                    created_at text not null default current_timestamp
                )
                """
            )

    def get(self, plugin_id: str) -> PluginRecord | None:
        with self._connect() as conn:
            row = conn.execute("select * from plugins where id = ?", (plugin_id,)).fetchone()
        return _record_from_row(row) if row else None

    def list(self) -> list[PluginRecord]:
        with self._connect() as conn:
            rows = conn.execute("select * from plugins order by name").fetchall()
        return [_record_from_row(row) for row in rows]

    def list_enabled(self) -> list[PluginRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "select * from plugins where status = 'enabled' order by menu_order, name"
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def upsert(
        self,
        manifest: PluginManifest,
        *,
        status: str,
        install_path: Path,
        data_path: Path,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into plugins (
                    id, name, version, description, status, api_version,
                    permissions_json, menu_title, menu_icon, menu_order,
                    frontend_entry, backend_entry, backend_factory, install_path, data_path
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                    name = excluded.name,
                    version = excluded.version,
                    description = excluded.description,
                    status = excluded.status,
                    api_version = excluded.api_version,
                    permissions_json = excluded.permissions_json,
                    menu_title = excluded.menu_title,
                    menu_icon = excluded.menu_icon,
                    menu_order = excluded.menu_order,
                    frontend_entry = excluded.frontend_entry,
                    backend_entry = excluded.backend_entry,
                    backend_factory = excluded.backend_factory,
                    install_path = excluded.install_path,
                    data_path = excluded.data_path,
                    updated_at = current_timestamp
                """,
                (
                    manifest.id,
                    manifest.name,
                    manifest.version,
                    manifest.description,
                    status,
                    manifest.api_version,
                    json.dumps(list(manifest.permissions)),
                    manifest.menu.title,
                    manifest.menu.icon,
                    manifest.menu.order,
                    manifest.frontend.entry,
                    manifest.backend.entry if manifest.backend else None,
                    manifest.backend.factory if manifest.backend else None,
                    str(install_path),
                    str(data_path),
                ),
            )

    def set_status(self, plugin_id: str, status: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "update plugins set status = ?, updated_at = current_timestamp where id = ?",
                (status, plugin_id),
            )
            return cursor.rowcount > 0

    def delete(self, plugin_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("delete from plugins where id = ?", (plugin_id,))
            return cursor.rowcount > 0

    def log(
        self,
        *,
        plugin_id: str | None,
        operation: str,
        status: str,
        message: str,
        detail: dict[str, object] | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into plugin_operation_logs
                    (plugin_id, operation, status, message, detail_json)
                values (?, ?, ?, ?, ?)
                """,
                (plugin_id, operation, status, message, json.dumps(detail or {})),
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _ensure_plugin_columns(conn: sqlite3.Connection) -> None:
        rows = conn.execute("pragma table_info(plugins)").fetchall()
        existing = {row["name"] for row in rows}
        columns = {
            "menu_title": "text not null default ''",
            "menu_icon": "text",
            "menu_order": "integer not null default 1000",
            "frontend_entry": "text not null default ''",
            "backend_entry": "text",
            "backend_factory": "text",
        }
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(f"alter table plugins add column {name} {ddl}")


def _record_from_row(row: sqlite3.Row) -> PluginRecord:
    return PluginRecord(
        id=row["id"],
        name=row["name"],
        version=row["version"],
        description=row["description"],
        status=row["status"],
        api_version=row["api_version"],
        permissions=tuple(json.loads(row["permissions_json"])),
        menu_title=row["menu_title"],
        menu_icon=row["menu_icon"],
        menu_order=row["menu_order"],
        frontend_entry=row["frontend_entry"],
        backend_entry=row["backend_entry"],
        backend_factory=row["backend_factory"],
        install_path=row["install_path"],
        data_path=row["data_path"],
    )
