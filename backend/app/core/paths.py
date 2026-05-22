from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    data: Path
    installed_plugins: Path
    plugin_data: Path
    temp: Path

    @classmethod
    def from_project_root(cls, root: Path) -> "RuntimePaths":
        data = root / "data"
        return cls.from_data_dir(root=root, data=data)

    @classmethod
    def from_data_dir(cls, *, root: Path, data: Path) -> "RuntimePaths":
        return cls(
            root=root,
            data=data,
            installed_plugins=data / "installed_plugins",
            plugin_data=data / "plugin_data",
            temp=data / "tmp",
        )

    def ensure(self) -> None:
        self.data.mkdir(parents=True, exist_ok=True)
        self.installed_plugins.mkdir(parents=True, exist_ok=True)
        self.plugin_data.mkdir(parents=True, exist_ok=True)
        self.temp.mkdir(parents=True, exist_ok=True)

    def install_dir(self, plugin_id: str, version: str) -> Path:
        return self.installed_plugins / plugin_id / version

    def data_dir(self, plugin_id: str) -> Path:
        return self.plugin_data / plugin_id
