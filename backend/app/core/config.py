from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SshExecutorMode = Literal["paramiko", "fake"]


@dataclass(frozen=True)
class AppConfig:
    ssh_executor: SshExecutorMode = "paramiko"
    data_dir: Path | None = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        raw_mode = os.getenv("CYTOOL_SSH_EXECUTOR", "paramiko").strip().lower()
        if raw_mode not in {"paramiko", "fake"}:
            raw_mode = "paramiko"
        raw_data_dir = os.getenv("CYTOOL_DATA_DIR")
        return cls(
            ssh_executor=raw_mode,  # type: ignore[arg-type]
            data_dir=Path(raw_data_dir) if raw_data_dir else None,
        )
