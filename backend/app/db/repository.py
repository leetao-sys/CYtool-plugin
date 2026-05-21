from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterator

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
    install_path: str
    data_path: str


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
                    install_path text not null,
                    data_path text not null,
                    created_at text not null default current_timestamp,
                    updated_at text not null default current_timestamp
                )
                """
            )
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
                    permissions_json, install_path, data_path
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                    name = excluded.name,
                    version = excluded.version,
                    description = excluded.description,
                    status = excluded.status,
                    api_version = excluded.api_version,
                    permissions_json = excluded.permissions_json,
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


def _record_from_row(row: sqlite3.Row) -> PluginRecord:
    return PluginRecord(
        id=row["id"],
        name=row["name"],
        version=row["version"],
        description=row["description"],
        status=row["status"],
        api_version=row["api_version"],
        permissions=tuple(json.loads(row["permissions_json"])),
        install_path=row["install_path"],
        data_path=row["data_path"],
    )
