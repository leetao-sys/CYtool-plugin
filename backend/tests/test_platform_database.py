from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app.db.repository import PluginRepository
from app.platform_api.database import CrudRequest, DatabaseConnection, DatabaseService, QueryRequest
from app.platform_api.errors import PermissionDeniedError
from app.platform_api.permissions import PluginPermissionService
from app.plugins.manifest import PluginManifest


class DatabaseServiceTests(unittest.TestCase):
    def create_service(self, root: Path, permissions: list[str]) -> tuple[DatabaseService, Path]:
        repo = PluginRepository(root / "cytool.sqlite3")
        repo.initialize()
        manifest = PluginManifest.from_dict(
            {
                "id": "db-plugin",
                "name": "DB Plugin",
                "version": "1.0.0",
                "description": "DB",
                "api_version": "1.0",
                "frontend": {"entry": "frontend/index.html"},
                "menu": {"title": "DB"},
                "permissions": permissions,
            }
        )
        repo.upsert(
            manifest,
            status="enabled",
            install_path=root / "installed",
            data_path=root / "data",
        )
        db_path = root / "target.sqlite3"
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("create table users (id integer primary key, name text)")
            conn.execute("insert into users (name) values ('alice')")
            conn.commit()
        return DatabaseService(PluginPermissionService(repo)), db_path

    def test_read_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service, db_path = self.create_service(root, ["database:read"])
            result = service.execute_query(
                QueryRequest(
                    plugin_id="db-plugin",
                    connection=DatabaseConnection(type="sqlite", database=str(db_path)),
                    operation="read",
                    sql="select name from users",
                )
            )
            self.assertEqual(result["rows"], [["alice"]])

    def test_write_requires_permission(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service, db_path = self.create_service(root, ["database:read"])
            with self.assertRaises(PermissionDeniedError):
                service.execute_crud(
                    CrudRequest(
                        plugin_id="db-plugin",
                        connection=DatabaseConnection(type="sqlite", database=str(db_path)),
                        table="users",
                        action="insert",
                        data={"name": "bob"},
                    )
                )

    def test_crud_insert_and_select(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service, db_path = self.create_service(root, ["database:read", "database:write"])
            service.execute_crud(
                CrudRequest(
                    plugin_id="db-plugin",
                    connection=DatabaseConnection(type="sqlite", database=str(db_path)),
                    table="users",
                    action="insert",
                    data={"name": "bob"},
                )
            )
            result = service.execute_crud(
                CrudRequest(
                    plugin_id="db-plugin",
                    connection=DatabaseConnection(type="sqlite", database=str(db_path)),
                    table="users",
                    action="select",
                    where={"name": "bob"},
                )
            )
            self.assertEqual(result["rows"][0][1], "bob")


if __name__ == "__main__":
    unittest.main()
