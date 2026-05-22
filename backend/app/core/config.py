from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

SshExecutorMode = Literal["paramiko", "fake"]


@dataclass(frozen=True)
class AppConfig:
    ssh_executor: SshExecutorMode = "paramiko"

    @classmethod
    def from_env(cls) -> "AppConfig":
        raw_mode = os.getenv("CYTOOL_SSH_EXECUTOR", "paramiko").strip().lower()
        if raw_mode not in {"paramiko", "fake"}:
            raw_mode = "paramiko"
        return cls(ssh_executor=raw_mode)  # type: ignore[arg-type]

