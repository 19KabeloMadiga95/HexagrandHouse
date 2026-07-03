from pathlib import Path
from datetime import datetime
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

ARCHIVE_DIR = (
    PROJECT_ROOT
    / "_archive"
    / f"cleanup_phase1_{datetime.now():%Y%m%d_%H%M%S}"
)

TARGETS = [
    SRC_DIR / "common",
    SRC_DIR / "config",
    SRC_DIR / "database",
    SRC_DIR / "football" / "frontend",
]


def archive_path(path: Path):
    if not path.exists():
        print(f"[SKIP] Missing: {path}")
        return

    relative_path = path.relative_to(PROJECT_ROOT)
    destination = ARCHIVE_DIR / relative_path

    destination.parent.mkdir(parents=True, exist_ok=True)

    print(f"[ARCHIVE] {relative_path} -> {destination.relative_to(PROJECT_ROOT)}")
    shutil.move(str(path), str(destination))


def main():
    print("======================================")
    print("HEXAGRANDHOUSE CLEANUP PHASE 1")
    print("Archive duplicate infrastructure")
    print("======================================")

    for target in TARGETS:
        archive_path(target)

    print("======================================")
    print("DONE")
    print(f"Archive folder: {ARCHIVE_DIR}")
    print("======================================")


if __name__ == "__main__":
    main()