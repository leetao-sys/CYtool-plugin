from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.db.repository import PluginRepository
from app.platform_api.permissions import PluginPermissionService
from app.platform_api.ssh import (
    BecomeConfig,
    ParamikoSshExecutor,
    SshBatchCommandRequest,
    SshCommandRequest,
    SshHost,
    SshService,
)
from app.plugins.manifest import PluginManifest


class SshServiceTests(unittest.TestCase):
    def create_service(self, root: Path) -> SshService:
        repo = PluginRepository(root / "cytool.sqlite3")
        repo.initialize()
        manifest = PluginManifest.from_dict(
            {
                "id": "ssh-plugin",
                "name": "SSH Plugin",
                "version": "1.0.0",
                "description": "SSH",
                "api_version": "1.0",
                "frontend": {"entry": "frontend/index.html"},
                "menu": {"title": "SSH"},
                "permissions": ["ssh:command", "ssh:batch"],
            }
        )
        repo.upsert(
            manifest,
            status="enabled",
            install_path=root / "installed",
            data_path=root / "data",
        )
        return SshService(PluginPermissionService(repo))

    def test_execute_with_su_become(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = self.create_service(Path(temp))
            result = service.execute(
                SshCommandRequest(
                    plugin_id="ssh-plugin",
                    host=SshHost(
                        host="127.0.0.1",
                        username="user",
                        password="secret",
                        become=BecomeConfig(enabled=True, method="su", target_user="root"),
                    ),
                    command="whoami",
                )
            )
            self.assertIn("[become:su:root]", result["stdout"])

    def test_execute_with_sudo_become(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = self.create_service(Path(temp))
            result = service.execute(
                SshCommandRequest(
                    plugin_id="ssh-plugin",
                    host=SshHost(
                        host="127.0.0.1",
                        username="user",
                        password="secret",
                        become=BecomeConfig(enabled=True, method="sudo", target_user="root"),
                    ),
                    command="id",
                )
            )
            self.assertIn("[become:sudo:root]", result["stdout"])

    def test_batch_execute(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = self.create_service(Path(temp))
            result = service.batch_execute(
                SshBatchCommandRequest(
                    plugin_id="ssh-plugin",
                    hosts=(
                        SshHost(host="host1", username="user", password="secret"),
                        SshHost(host="host2", username="user", password="secret"),
                    ),
                    command="hostname",
                )
            )
            self.assertEqual(len(result["results"]), 2)


class ParamikoExecutorTests(unittest.TestCase):
    def test_plain_command_uses_exec_command(self) -> None:
        client = FakeParamikoClient(stdout=b"ok\n", stderr=b"", exit_code=0)
        executor = ParamikoSshExecutor(client_factory=lambda: client)

        result = executor.execute(
            SshHost(host="server", username="user", password="secret"),
            "hostname",
            30,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "ok\n")
        self.assertEqual(client.exec_commands[0]["command"], "hostname")
        self.assertTrue(client.closed)

    def test_sudo_command_writes_password_and_wraps_command(self) -> None:
        client = FakeParamikoClient(stdout=b"root\n", stderr=b"", exit_code=0)
        executor = ParamikoSshExecutor(client_factory=lambda: client)

        result = executor.execute(
            SshHost(
                host="server",
                username="user",
                password="secret",
                become=BecomeConfig(
                    enabled=True,
                    method="sudo",
                    target_user="root",
                    password="root-secret",
                ),
            ),
            "whoami",
            30,
        )

        self.assertTrue(result.success)
        self.assertIn("sudo -S", client.exec_commands[0]["command"])
        self.assertEqual(client.stdin.writes, ["root-secret\n"])

    def test_su_command_uses_interactive_shell_and_reads_marker(self) -> None:
        channel = FakeShellChannel(
            b"Password:\nroot\n__CYTOOL_EXIT_123__0\n",
        )
        client = FakeParamikoClient(shell_channel=channel)
        executor = ParamikoSshExecutor(client_factory=lambda: client)

        result = executor.execute(
            SshHost(
                host="server",
                username="user",
                password="secret",
                become=BecomeConfig(enabled=True, method="su", target_user="root", password="pw"),
            ),
            "whoami",
            30,
        )

        self.assertTrue(result.success)
        self.assertIn("su - root", channel.sent)
        self.assertIn("whoami", channel.sent)


class FakeStream:
    def __init__(self, content: bytes = b"", exit_code: int = 0) -> None:
        self.content = content
        self.channel = self
        self.exit_code = exit_code
        self.writes: list[str] = []
        self.closed = False

    def read(self) -> bytes:
        return self.content

    def recv_exit_status(self) -> int:
        return self.exit_code

    def write(self, value: str) -> None:
        self.writes.append(value)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class FakeShellChannel:
    def __init__(self, output: bytes) -> None:
        self.output = output
        self.sent = ""
        self.timeout = None
        self.consumed = False

    def settimeout(self, timeout: int) -> None:
        self.timeout = timeout

    def send(self, value: str) -> None:
        self.sent += value
        marker_start = value.find("__CYTOOL_EXIT_")
        if marker_start >= 0:
            marker = value[marker_start:].split("%s", 1)[0]
            self.output = self.output.replace(b"__CYTOOL_EXIT_123__", marker.encode())

    def recv_ready(self) -> bool:
        return not self.consumed

    def recv(self, size: int) -> bytes:
        if self.consumed:
            return b""
        self.consumed = True
        return self.output


class FakeParamikoClient:
    def __init__(
        self,
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        exit_code: int = 0,
        shell_channel: FakeShellChannel | None = None,
    ) -> None:
        self.stdin = FakeStream()
        self.stdout = FakeStream(stdout, exit_code)
        self.stderr = FakeStream(stderr, exit_code)
        self.shell_channel = shell_channel or FakeShellChannel(b"")
        self.exec_commands: list[dict[str, object]] = []
        self.connect_kwargs: dict[str, object] | None = None
        self.closed = False

    def connect(self, **kwargs: object) -> None:
        self.connect_kwargs = kwargs

    def exec_command(self, command: str, **kwargs: object):
        self.exec_commands.append({"command": command, **kwargs})
        return self.stdin, self.stdout, self.stderr

    def invoke_shell(self):
        return self.shell_channel

    def close(self) -> None:
        self.closed = True


if __name__ == "__main__":
    unittest.main()
