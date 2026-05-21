from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import PackageValidationError
from .manifest import PluginManifest


@dataclass(frozen=True)
class ValidatedPluginPackage:
    archive_path: Path
    manifest: PluginManifest
    file_names: tuple[str, ...]


class PluginPackageValidator:
    def __init__(self, *, max_size_bytes: int = 50 * 1024 * 1024, max_files: int = 2000) -> None:
        self.max_size_bytes = max_size_bytes
        self.max_files = max_files

    def validate(self, archive_path: Path) -> ValidatedPluginPackage:
        if archive_path.suffix.lower() != ".zip":
            raise PackageValidationError("plugin package must be a .zip file")
        if not archive_path.exists():
            raise PackageValidationError("plugin package does not exist")
        if archive_path.stat().st_size > self.max_size_bytes:
            raise PackageValidationError("plugin package is too large")

        try:
            with zipfile.ZipFile(archive_path) as archive:
                infos = archive.infolist()
                if len(infos) > self.max_files:
                    raise PackageValidationError("plugin package contains too many files")
                names = tuple(info.filename for info in infos if not info.is_dir())
                for name in names:
                    _validate_zip_member_name(name)
                if "plugin.json" not in names:
                    raise PackageValidationError("plugin package must contain plugin.json")
                manifest = PluginManifest.from_json(archive.read("plugin.json").decode("utf-8"))
                self._ensure_declared_files_exist(manifest, names)
        except zipfile.BadZipFile as exc:
            raise PackageValidationError("plugin package is not a valid zip archive") from exc

        return ValidatedPluginPackage(
            archive_path=archive_path,
            manifest=manifest,
            file_names=names,
        )

    def extract_to(self, package: ValidatedPluginPackage, destination: Path) -> None:
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=False)
        try:
            with zipfile.ZipFile(package.archive_path) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    _validate_zip_member_name(info.filename)
                    target = destination / PurePosixPath(info.filename)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise

    @staticmethod
    def _ensure_declared_files_exist(manifest: PluginManifest, names: tuple[str, ...]) -> None:
        if manifest.frontend.entry not in names:
            raise PackageValidationError("frontend.entry does not exist in plugin package")
        if manifest.backend and manifest.backend.entry not in names:
            raise PackageValidationError("backend.entry does not exist in plugin package")


def _validate_zip_member_name(name: str) -> None:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise PackageValidationError(f"unsafe zip entry path: {name}")
    if normalized.startswith("/") or ":" in path.parts[0]:
        raise PackageValidationError(f"unsafe zip entry path: {name}")

