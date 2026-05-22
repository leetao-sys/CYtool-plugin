from __future__ import annotations

import shutil
from pathlib import Path

from app.core.paths import RuntimePaths
from app.db.repository import PluginRepository, PluginRecord

from .errors import PluginConflictError, PluginNotFoundError
from .package import PluginPackageValidator
from .version import Version


class PluginLifecycleService:
    def __init__(
        self,
        *,
        paths: RuntimePaths,
        repository: PluginRepository,
        package_validator: PluginPackageValidator | None = None,
    ) -> None:
        self.paths = paths
        self.repository = repository
        self.package_validator = package_validator or PluginPackageValidator()

    def list(self) -> list[PluginRecord]:
        self.repository.initialize()
        return self.repository.list()

    def enabled_menus(self) -> list[dict[str, object]]:
        self.repository.initialize()
        return [record.to_menu_dict() for record in self.repository.list_enabled()]

    def logs(self, plugin_id: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        self.repository.initialize()
        return [record.to_dict() for record in self.repository.list_logs(plugin_id, limit)]

    def install(self, archive_path: Path) -> PluginRecord:
        self.paths.ensure()
        self.repository.initialize()

        package = self.package_validator.validate(archive_path)
        manifest = package.manifest
        if self.repository.get(manifest.id):
            raise PluginConflictError("plugin already exists; use update instead")

        install_dir = self.paths.install_dir(manifest.id, manifest.version)
        data_dir = self.paths.data_dir(manifest.id)
        staging_dir = self.paths.temp / f"{manifest.id}-{manifest.version}.staging"

        self.package_validator.extract_to(package, staging_dir)
        install_dir.parent.mkdir(parents=True, exist_ok=True)
        if install_dir.exists():
            shutil.rmtree(install_dir)
        shutil.move(str(staging_dir), str(install_dir))
        data_dir.mkdir(parents=True, exist_ok=True)

        self.repository.upsert(
            manifest,
            status="enabled",
            install_path=install_dir,
            data_path=data_dir,
        )
        self.repository.log(
            plugin_id=manifest.id,
            operation="install",
            status="success",
            message=f"Installed plugin {manifest.id} {manifest.version}",
        )
        record = self.repository.get(manifest.id)
        if record is None:
            raise PluginNotFoundError("plugin was installed but metadata could not be loaded")
        return record

    def update(self, archive_path: Path) -> PluginRecord:
        self.paths.ensure()
        self.repository.initialize()

        package = self.package_validator.validate(archive_path)
        manifest = package.manifest
        current = self.repository.get(manifest.id)
        if not current:
            raise PluginNotFoundError("plugin not found; install it first")
        if manifest.parsed_version <= Version.parse(current.version):
            raise PluginConflictError("plugin update version must be newer than current version")

        install_dir = self.paths.install_dir(manifest.id, manifest.version)
        data_dir = Path(current.data_path)
        staging_dir = self.paths.temp / f"{manifest.id}-{manifest.version}.staging"

        self.package_validator.extract_to(package, staging_dir)
        install_dir.parent.mkdir(parents=True, exist_ok=True)
        if install_dir.exists():
            shutil.rmtree(install_dir)
        shutil.move(str(staging_dir), str(install_dir))
        data_dir.mkdir(parents=True, exist_ok=True)

        self.repository.upsert(
            manifest,
            status=current.status,
            install_path=install_dir,
            data_path=data_dir,
        )
        self.repository.log(
            plugin_id=manifest.id,
            operation="update",
            status="success",
            message=f"Updated plugin {manifest.id} from {current.version} to {manifest.version}",
        )
        record = self.repository.get(manifest.id)
        if record is None:
            raise PluginNotFoundError("plugin was updated but metadata could not be loaded")
        return record

    def enable(self, plugin_id: str) -> None:
        if not self.repository.set_status(plugin_id, "enabled"):
            raise PluginNotFoundError("plugin not found")
        self.repository.log(
            plugin_id=plugin_id,
            operation="enable",
            status="success",
            message=f"Enabled plugin {plugin_id}",
        )

    def disable(self, plugin_id: str) -> None:
        if not self.repository.set_status(plugin_id, "disabled"):
            raise PluginNotFoundError("plugin not found")
        self.repository.log(
            plugin_id=plugin_id,
            operation="disable",
            status="success",
            message=f"Disabled plugin {plugin_id}",
        )

    def uninstall(self, plugin_id: str) -> None:
        record = self.repository.get(plugin_id)
        if not record:
            raise PluginNotFoundError("plugin not found")
        shutil.rmtree(record.install_path, ignore_errors=True)
        self.repository.delete(plugin_id)
        self.repository.log(
            plugin_id=plugin_id,
            operation="uninstall",
            status="success",
            message=f"Uninstalled plugin {plugin_id}",
        )
