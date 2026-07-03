from pathlib import Path
import shutil
from datetime import datetime

from src.core.logging import info, warning


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent_directory(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def folder_exists(path: Path) -> bool:
    return path.exists() and path.is_dir()


def backup_file(
    source_file: Path,
    backup_root: Path,
) -> Path | None:
    if not source_file.exists():
        warning(f"Cannot backup missing file: {source_file}")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_file = (
        backup_root
        / timestamp
        / source_file.name
    )

    target_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target_file)

    info(f"Backup created: {target_file}")
    return target_file


def safe_copy(
    source: Path,
    target: Path,
    overwrite: bool = True,
) -> bool:
    if not source.exists():
        warning(f"Source missing: {source}")
        return False

    if target.exists() and not overwrite:
        warning(f"Target exists, skipped: {target}")
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

    info(f"Copied {source} -> {target}")
    return True