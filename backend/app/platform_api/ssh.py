from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal, Protocol

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

