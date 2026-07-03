from pathlib import Path
from datetime import datetime
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

ARCHIVE_DIR = PROJECT_ROOT / "_archive" / f"final_cleanup_{datetime.now():%Y%m%d_%H%M%S}"

TARGETS_TO_ARCHIVE = [
    SRC_DIR / "common",
    SRC_DIR / "config",
    SRC_DIR / "database",
    SRC_DIR / "football" / "frontend",
    SRC_DIR / "lottery" / "frontend",
    SRC_DIR / "services" / "analytics_service.py",
    SRC_DIR / "services" / "health_service.py",
]

LEGACY_PATTERNS = [
    "src.common",
    "src.config",
    "src.database",
    "src.lottery.frontend",
    "lottery.frontend",
]


def archive_target(path: Path):
    if not path.exists():
        print(f"[OK] Already removed: {path.relative_to(PROJECT_ROOT)}")
        return

    destination = ARCHIVE_DIR / path.relative_to(PROJECT_ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(destination))
    print(f"[ARCHIVED] {path.relative_to(PROJECT_ROOT)}")


def remove_pycache():
    for folder in SRC_DIR.rglob("__pycache__"):
        shutil.rmtree(folder, ignore_errors=True)
        print(f"[REMOVED CACHE] {folder.relative_to(PROJECT_ROOT)}")


def scan_legacy_imports():
    print("\nLegacy reference scan:")

    matches = []

    for file in SRC_DIR.rglob("*.py"):
        text = file.read_text(encoding="utf-8", errors="ignore")

        for pattern in LEGACY_PATTERNS:
            if pattern in text:
                matches.append((file, pattern))

    if not matches:
        print("[OK] No legacy references found.")
        return

    for file, pattern in matches:
        print(f"[CHECK] {file.relative_to(PROJECT_ROOT)} contains {pattern}")


def main():
    print("======================================")
    print("HEXAGRANDHOUSE FINAL CLEANUP")
    print("======================================")

    for target in TARGETS_TO_ARCHIVE:
        archive_target(target)

    remove_pycache()
    scan_legacy_imports()

    print("\nFinal expected src folders:")
    for folder in sorted([p.name for p in SRC_DIR.iterdir() if p.is_dir()]):
        print(f"- {folder}")

    print("======================================")
    print("FINAL CLEANUP COMPLETE")
    print("======================================")


if __name__ == "__main__":
    main()