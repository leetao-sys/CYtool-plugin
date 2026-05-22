from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from app.db.repository import PluginRecord

from .errors import PluginError


@dataclass(frozen=True)
class PluginContext:
    plugin_id: str
    install_path: Path
    data_path: Path
    api_version: str


@dataclass(frozen=True)
class LoadedPluginBackend:
    plugin_id: str
    module: ModuleType
    instance: Any


class PluginBackendLoader:
    def load(self, record: PluginRecord) -> LoadedPluginBackend | None:
        if not record.backend_entry:
            return None

        install_path = Path(record.install_path)
        backend_path = install_path / record.backend_entry
        if not backend_path.exists():
            raise PluginError("plugin backend entry file does not exist")

        module_name = f"cytool_plugin_{record.id.replace('-', '_').replace('.', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, backend_path)
        if spec is None or spec.loader is None:
            raise PluginError("failed to create plugin backend import spec")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        factory_name = record.backend_factory or "create_plugin"
        factory = getattr(module, factory_name, None)
        if not callable(factory):
            raise PluginError(f"plugin backend factory {factory_name!r} is not callable")

        context = PluginContext(
            plugin_id=record.id,
            install_path=install_path,
            data_path=Path(record.data_path),
            api_version=record.api_version,
        )
        instance = factory(context)
        return LoadedPluginBackend(plugin_id=record.id, module=module, instance=instance)

