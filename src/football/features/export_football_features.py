from __future__ import annotations

from datetime import datetime
import pandas as pd

from src.football.features.build_football_features import build_football_features


# =========================================================
# SQLITE-FIRST FOOTBALL FEATURE EXPORT
# =========================================================

def export_football_features() -> pd.DataFrame:
    """
    Build and persist football feature tables in SQLite.

    This callable is used by the daily football automation cycle.
    It also keeps the module runnable with:
        python -m src.football.features.export_football_features
    """

    print("\n======================================")
    print("HEXAGRANDHOUSE FOOTBALL FEATURE EXPORT")
    print("SQLite-first runtime mode")
    print("======================================")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================")

    match_features = build_football_features()

    row_count = len(match_features) if isinstance(match_features, pd.DataFrame) else 0

    print("\n======================================")
    print("FOOTBALL FEATURE EXPORT COMPLETE")
    print("======================================")
    print(f"Rows: {row_count}")
    print("======================================\n")

    return match_features


def main() -> pd.DataFrame:
    return export_football_features()


if __name__ == "__main__":
    main()
