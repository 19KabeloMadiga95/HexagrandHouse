from pathlib import Path
from datetime import datetime
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

# Files that should NEVER be rewritten by this tool
SKIP_PATHS = {
    "src/data/database.py",
    "src/data/query_service.py",
    "src/data/build_database.py",
}

BACKUP_DIR = (
    PROJECT_ROOT
    / "_archive"
    / f"import_migration_backup_{datetime.now():%Y%m%d_%H%M%S}"
)

DRY_RUN = False


REPLACEMENTS = {
    "from src.database.database_connection import": "from src.data.database import",
    "from database.database_connection import": "from src.data.database import",
    "from src.database.query_service import": "from src.data.query_service import",
    "from database.query_service import": "from src.data.query_service import",
    "from src.database.build_hexagrandhouse_db import": "from src.data.build_database import",
    "from database.build_hexagrandhouse_db import": "from src.data.build_database import",
}


def backup_file(file_path: Path):
    relative_path = file_path.relative_to(PROJECT_ROOT)
    backup_path = BACKUP_DIR / relative_path

    if DRY_RUN:
        print(f"[DRY RUN] backup {relative_path}")
        return

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, backup_path)


def migrate_file(file_path: Path) -> bool:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    original_text = text

    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)

    if text == original_text:
        return False

    relative_path = file_path.relative_to(PROJECT_ROOT)

    print(f"[CHANGE] {relative_path}")

    backup_file(file_path)

    if not DRY_RUN:
        file_path.write_text(text, encoding="utf-8")

    return True


def main():
    changed_count = 0
    scanned_count = 0

    print("======================================")
    print("HEXAGRANDHOUSE IMPORT MIGRATION")
    print("======================================")
    print(f"DRY_RUN: {DRY_RUN}")
    print(f"SRC_DIR: {SRC_DIR}")
    print("======================================")

    for file_path in SRC_DIR.rglob("*.py"):

        if "__pycache__" in file_path.parts:
            continue

        relative_path = (
            str(file_path.relative_to(PROJECT_ROOT))
            .replace("\\", "/")
        )

        if relative_path in SKIP_PATHS:
            print(f"[SKIP WRAPPER] {relative_path}")
            continue

        scanned_count += 1

        if migrate_file(file_path):
            changed_count += 1

    print("======================================")
    print("IMPORT MIGRATION COMPLETE")
    print("======================================")
    print(f"Files scanned : {scanned_count}")
    print(f"Files changed : {changed_count}")

    if DRY_RUN:
        print("No files were modified. Set DRY_RUN = False to apply.")
    else:
        print(f"Backups saved to: {BACKUP_DIR}")

    print("======================================")


if __name__ == "__main__":
    main()