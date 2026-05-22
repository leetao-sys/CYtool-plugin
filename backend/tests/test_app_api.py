from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import AppConfig
from app.core.paths import RuntimePaths
from app.main import create_app

from helpers import write_plugin_zip


class AppApiTests(unittest.TestCase):
    def create_client(self, root: Path) -> TestClient:
        paths = RuntimePaths.from_project_root(root)
        app = create_app(config=AppConfig(ssh_executor="fake"), paths=paths)
        return TestClient(app)

    def test_upload_menu_disable_enable_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = write_plugin_zip(root)
            client = self.create_client(root)

            with archive.open("rb") as file:
                upload = client.post(
                    "/api/admin/plugins/upload",
                    files={"file": ("json_formatter.zip", file, "application/zip")},
                )
            self.assertEqual(upload.status_code, 200)
            self.assertEqual(upload.json()["plugin"]["id"], "json-formatter")

            menus = client.get("/api/runtime/menus")
            self.assertEqual(menus.status_code, 200)
            self.assertEqual(menus.json()[0]["plugin_id"], "json-formatter")

            index = client.get("/plugins/json-formatter/index.html")
            self.assertEqual(index.status_code, 200)

            backend = client.post(
                "/api/runtime/plugins/json-formatter/backend/echo",
                json={"payload": {"hello": "world"}},
            )
            self.assertEqual(backend.status_code, 200)
            self.assertEqual(backend.json()["result"]["payload"], {"hello": "world"})

            disabled = client.post("/api/admin/plugins/json-formatter/disable")
            self.assertEqual(disabled.status_code, 200)
            self.assertEqual(client.get("/api/runtime/menus").json(), [])
            self.assertGreaterEqual(
                len(client.get("/api/admin/plugins/json-formatter/logs").json()),
                1,
            )

            enabled = client.post("/api/admin/plugins/json-formatter/enable")
            self.assertEqual(enabled.status_code, 200)
            self.assertEqual(len(client.get("/api/runtime/menus").json()), 1)

            deleted = client.delete("/api/admin/plugins/json-formatter")
            self.assertEqual(deleted.status_code, 200)
            self.assertEqual(client.get("/api/admin/plugins").json(), [])


if __name__ == "__main__":
    unittest.main()
