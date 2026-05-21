from __future__ import annotations

import io
import time
from dataclasses import dataclass
from typing import Literal, Protocol

from .errors import SshApiError
from .permissions import PluginPermissionService

AuthType = Literal["password", "private_key"]
BecomeMethod = Literal["su", "sudo"]


@dataclass(frozen=True)
class BecomeConfig:
    enabled: bool = False
    method: BecomeMethod = "su"
    target_user: str = "root"
    password: str | None = None


@dataclass(frozen=True)
class SshHost:
    host: str
    port: int = 22
    username: str = ""
    password: str | None = None
    private_key: str | None = None
    auth_type: AuthType = "password"
    become: BecomeConfig | None = None


@dataclass(frozen=True)
class SshCommandRequest:
    plugin_id: str
    host: SshHost
    command: str
    timeout_seconds: int = 30


@dataclass(frozen=True)
class SshBatchCommandRequest:
    plugin_id: str
    hosts: tuple[SshHost, ...]
    command: str
    concurrency: int = 5
    timeout_seconds: int = 30


@dataclass(frozen=True)
class SshCommandResult:
    success: bool
    host: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float

    def to_dict(self) -> dict[str, object]:
        return {
            "success": self.success,
            "host": self.host,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
        }


class SshExecutor(Protocol):
    def execute(self, host: SshHost, command: str, timeout_seconds: int) -> SshCommandResult:
        ...


class FakeSshExecutor:
    def execute(self, host: SshHost, command: str, timeout_seconds: int) -> SshCommandResult:
        start = time.perf_counter()
        become = host.become
        prefix = ""
        if become and become.enabled:
            prefix = f"[become:{become.method}:{become.target_user}] "
        return SshCommandResult(
            success=True,
            host=host.host,
            stdout=f"{prefix}{command}\n",
            stderr="",
            exit_code=0,
            duration_ms=round((time.perf_counter() - start) * 1000, 3),
        )


class ParamikoSshExecutor:
    def __init__(self, *, client_factory: object | None = None) -> None:
        self.client_factory = client_factory

    def execute(self, host: SshHost, command: str, timeout_seconds: int) -> SshCommandResult:
        start = time.perf_counter()
        client = self._create_client()
        try:
            self._connect(client, host, timeout_seconds)
            become = host.become
            if become and become.enabled:
                if become.method == "sudo":
                    stdout, stderr, exit_code = self._execute_with_sudo(
                        client,
                        command,
                        become,
                        timeout_seconds,
                    )
                elif become.method == "su":
                    stdout, stderr, exit_code = self._execute_with_su(
                        client,
                        command,
                        become,
                        timeout_seconds,
                    )
                else:
                    raise SshApiError("unsupported become method")
            else:
                stdout, stderr, exit_code = self._execute_plain(client, command, timeout_seconds)

            return SshCommandResult(
                success=exit_code == 0,
                host=host.host,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_ms=round((time.perf_counter() - start) * 1000, 3),
            )
        except SshApiError:
            raise
        except Exception as exc:
            raise SshApiError("SSH command execution failed", detail={"reason": str(exc)}) from exc
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    def _create_client(self):
        if self.client_factory is not None:
            if callable(self.client_factory):
                return self.client_factory()
            return self.client_factory

        try:
            import paramiko
        except ModuleNotFoundError as exc:
            raise SshApiError("Paramiko is not installed") from exc

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def _connect(self, client: object, host: SshHost, timeout_seconds: int) -> None:
        kwargs: dict[str, object] = {
            "hostname": host.host,
            "port": host.port,
            "username": host.username,
            "timeout": timeout_seconds,
            "banner_timeout": timeout_seconds,
            "auth_timeout": timeout_seconds,
            "look_for_keys": False,
            "allow_agent": False,
        }
        if host.auth_type == "password":
            kwargs["password"] = host.password
        elif host.auth_type == "private_key":
            kwargs["pkey"] = self._load_private_key(host.private_key)
        else:
            raise SshApiError("unsupported SSH auth_type")
        client.connect(**kwargs)  # type: ignore[attr-defined]

    @staticmethod
    def _load_private_key(private_key: str | None) -> object:
        if not private_key:
            raise SshApiError("private_key is required for private_key authentication")
        try:
            import paramiko
        except ModuleNotFoundError as exc:
            raise SshApiError("Paramiko is not installed") from exc
        try:
            return paramiko.RSAKey.from_private_key(io.StringIO(private_key))
        except Exception as exc:
            raise SshApiError("failed to parse private key") from exc

    @staticmethod
    def _execute_plain(
        client: object,
        command: str,
        timeout_seconds: int,
    ) -> tuple[str, str, int]:
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout_seconds)  # type: ignore[attr-defined]
        _close_if_possible(stdin)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode("utf-8", errors="replace"), stderr.read().decode(
            "utf-8",
            errors="replace",
        ), exit_code

    def _execute_with_sudo(
        self,
        client: object,
        command: str,
        become: BecomeConfig,
        timeout_seconds: int,
    ) -> tuple[str, str, int]:
        sudo_command = f"sudo -S -p '' -u {become.target_user} -- sh -lc {_shell_quote(command)}"
        stdin, stdout, stderr = client.exec_command(  # type: ignore[attr-defined]
            sudo_command,
            get_pty=True,
            timeout=timeout_seconds,
        )
        if become.password:
            stdin.write(become.password + "\n")
            flush = getattr(stdin, "flush", None)
            if callable(flush):
                flush()
        _close_if_possible(stdin)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode("utf-8", errors="replace"), stderr.read().decode(
            "utf-8",
            errors="replace",
        ), exit_code

    def _execute_with_su(
        self,
        client: object,
        command: str,
        become: BecomeConfig,
        timeout_seconds: int,
    ) -> tuple[str, str, int]:
        channel = client.invoke_shell()  # type: ignore[attr-defined]
        settimeout = getattr(channel, "settimeout", None)
        if callable(settimeout):
            settimeout(timeout_seconds)

        marker = f"__CYTOOL_EXIT_{int(time.time() * 1000)}__"
        script = (
            f"su - {become.target_user}\n"
            f"{become.password or ''}\n"
            f"{command}\n"
            f"printf '\\n{marker}%s\\n' $?\n"
            "exit\n"
            "exit\n"
        )
        channel.send(script)

        output = self._read_channel_until_marker(channel, marker, timeout_seconds)
        exit_code = _extract_marker_exit_code(output, marker)
        cleaned = _remove_marker_line(output, marker)
        return cleaned, "", exit_code

    @staticmethod
    def _read_channel_until_marker(channel: object, marker: str, timeout_seconds: int) -> str:
        chunks: list[str] = []
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            recv_ready = getattr(channel, "recv_ready", lambda: True)
            if recv_ready():
                data = channel.recv(4096)
                if not data:
                    break
                text = data.decode("utf-8", errors="replace")
                chunks.append(text)
                if marker in "".join(chunks):
                    return "".join(chunks)
            else:
                time.sleep(0.05)
        raise SshApiError("timed out while waiting for su command result")


class SshService:
    def __init__(self, permissions: PluginPermissionService, executor: SshExecutor | None = None) -> None:
        self.permissions = permissions
        self.executor = executor or FakeSshExecutor()

    def execute(self, request: SshCommandRequest) -> dict[str, object]:
        self.permissions.require(request.plugin_id, "ssh:command")
        _validate_host(request.host)
        if not request.command.strip():
            raise ValueError("command is required")
        return self.executor.execute(
            request.host,
            request.command,
            request.timeout_seconds,
        ).to_dict()

    def batch_execute(self, request: SshBatchCommandRequest) -> dict[str, object]:
        self.permissions.require(request.plugin_id, "ssh:batch")
        results = []
        for host in request.hosts:
            _validate_host(host)
            results.append(
                self.executor.execute(host, request.command, request.timeout_seconds).to_dict()
            )
        return {"success": True, "results": results}


def _validate_host(host: SshHost) -> None:
    if not host.host.strip():
        raise ValueError("host is required")
    if not 1 <= host.port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    if not host.username.strip():
        raise ValueError("username is required")
    if host.auth_type == "password" and host.password is None:
        raise ValueError("password is required for password authentication")
    if host.auth_type == "private_key" and host.private_key is None:
        raise ValueError("private_key is required for private_key authentication")
    if host.become and host.become.enabled:
        if host.become.method not in {"su", "sudo"}:
            raise ValueError("become method must be su or sudo")


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _close_if_possible(stream: object) -> None:
    close = getattr(stream, "close", None)
    if callable(close):
        close()


def _extract_marker_exit_code(output: str, marker: str) -> int:
    for line in output.splitlines():
        if line.startswith(marker):
            raw_exit_code = line.removeprefix(marker).strip()
            if raw_exit_code.isdigit():
                return int(raw_exit_code)
    raise SshApiError("su command output did not include an exit marker")


def _remove_marker_line(output: str, marker: str) -> str:
    return "\n".join(line for line in output.splitlines() if not line.startswith(marker))
