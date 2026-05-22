from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "plugins"
DIST_DIR = ROOT / "dist" / "plugins"


def package_plugin(plugin_dir: Path) -> Path:
    manifest = plugin_dir / "plugin.json"
    if not manifest.exists():
        raise RuntimeError(f"missing plugin.json: {plugin_dir}")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = DIST_DIR / f"{plugin_dir.name}.zip"
    if archive_path.exists():
        archive_path.unlink()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in plugin_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(plugin_dir).as_posix())
    return archive_path


def main() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    packages = [package_plugin(path) for path in sorted(SOURCE_DIR.iterdir()) if path.is_dir()]
    for package in packages:
        print(package)


if __name__ == "__main__":
    main()

