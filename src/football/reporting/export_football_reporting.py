from __future__ import annotations

from datetime import datetime
from typing import Any

from src.football.reporting.football_model_performance_dashboard import (
    export_football_model_performance_dashboard,
)
from src.football.reporting.top_plays_report import export_top_plays_report
from src.football.value.value_bet_engine import export_value_bets


# =========================================================
# SQLITE FOOTBALL REPORTING EXPORT
# =========================================================

def _safe_total(result: Any) -> int:
    if isinstance(result, dict):
        total = 0
        for value in result.values():
            try:
                total += int(value or 0)
            except Exception:
                continue
        return total

    try:
        return int(result or 0)
    except Exception:
        return 0


def export_football_reporting() -> dict[str, int]:
    started = datetime.now()

    print("\n======================================")
    print("HEXAGRANDHOUSE FOOTBALL REPORTING")
    print("SQLite-first runtime mode")
    print("======================================")
    print(f"Started: {started.strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================\n")

    sections: dict[str, int] = {}

    print("\n======================================")
    print("BUILDING: Model Performance")
    print("======================================")
    sections["Football Model Performance"] = _safe_total(export_football_model_performance_dashboard())

    print("\n======================================")
    print("BUILDING: Top Plays")
    print("======================================")
    sections["Top Plays Report"] = _safe_total(export_top_plays_report())

    print("\n======================================")
    print("BUILDING: Value Bets")
    print("======================================")
    sections["Value Bet Engine"] = _safe_total(export_value_bets())

    finished = datetime.now()
    duration = round((finished - started).total_seconds(), 2)
    total_rows = sum(sections.values())

    print("\n======================================")
    print("FOOTBALL REPORTING COMPLETE")
    print("======================================")
    print(f"Finished: {finished.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration} sec")
    print(f"Rows    : {total_rows}")
    print("======================================")

    return sections


def main() -> dict[str, int]:
    return export_football_reporting()


if __name__ == "__main__":
    main()
