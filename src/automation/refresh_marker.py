from datetime import datetime, timezone

from src.core.paths import DATA_DIR, ensure_directory
from src.core.logging import success


REFRESH_MARKER_FILE = DATA_DIR / "last_cloud_refresh.txt"


def write_refresh_marker():
    ensure_directory(DATA_DIR)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    REFRESH_MARKER_FILE.write_text(
        timestamp,
        encoding="utf-8"
    )

    success(f"Refresh marker written: {timestamp}")

    return REFRESH_MARKER_FILE


def main():
    write_refresh_marker()


if __name__ == "__main__":
    main()