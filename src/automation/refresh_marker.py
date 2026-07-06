from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.core.paths import DATA_DIR, ensure_directory
from src.core.logging import success
from src.data.sqlite_store import replace_sqlite_table, create_indexes


REFRESH_MARKER_FILE = DATA_DIR / "last_cloud_refresh.txt"
REFRESH_MARKER_TABLE = "platform_cloud_refresh_marker"


# =========================================================
# SQLITE-FIRST REFRESH MARKER
# =========================================================


def write_refresh_marker() -> pd.DataFrame:
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    timestamp_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    marker_df = pd.DataFrame(
        [
            {
                "MarkerName": "Last Cloud Refresh",
                "TimestampUTC": timestamp_utc,
                "TimestampLocal": timestamp_local,
                "Source": "SQLite Runtime",
            }
        ]
    )

    replace_sqlite_table(REFRESH_MARKER_TABLE, marker_df)
    create_indexes(REFRESH_MARKER_TABLE, ["MarkerName", "TimestampUTC"])

    # Temporary backwards-compatible marker. This is not a data dependency.
    ensure_directory(DATA_DIR)
    REFRESH_MARKER_FILE.write_text(timestamp_utc, encoding="utf-8")

    success(f"Refresh marker written to SQLite: {timestamp_utc}")

    return marker_df


def main() -> pd.DataFrame:
    return write_refresh_marker()


if __name__ == "__main__":
    main()
