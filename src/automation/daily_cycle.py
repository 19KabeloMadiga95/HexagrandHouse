from __future__ import annotations

import os
from typing import Callable

from src.core.pipeline import BasePipeline
from src.lottery.automation.run_daily_lottery_cycle import main as run_lottery_cycle
from src.automation.refresh_marker import main as write_refresh_marker


# =========================================================
# HEXAGRANDHOUSE DAILY CYCLE - SQLITE RUNTIME
# =========================================================


def _football_sqlite_placeholder() -> dict:
    """
    Football still has separate Excel-heavy model scripts.
    Until the football migration batch is complete, the production daily cycle
    keeps existing football SQLite tables as-is instead of rebuilding from Excel.
    """

    print("Football SQLite cycle not migrated yet. Existing SQLite football tables retained.")
    return {
        "Status": "Skipped",
        "Reason": "Football SQLite migration pending",
    }


def _optional_legacy_football_cycle() -> dict:
    """
    Disabled by default to avoid Excel runtime dependency.

    Set HGH_RUN_LEGACY_FOOTBALL_CYCLE=1 only when you intentionally want to run
    the old football Excel pipeline locally.
    """

    if os.getenv("HGH_RUN_LEGACY_FOOTBALL_CYCLE") != "1":
        return _football_sqlite_placeholder()

    from src.football.automation.run_daily_football_cycle import main as legacy_football_cycle

    return legacy_football_cycle()


def build_daily_cycle_pipeline() -> BasePipeline:
    pipeline = BasePipeline("HexagrandHouse Daily Cycle - SQLite Runtime")

    pipeline.add_step(
        name="Lottery SQLite Daily Cycle",
        function=run_lottery_cycle,
        required=True,
    )

    pipeline.add_step(
        name="Football SQLite Cycle",
        function=_optional_legacy_football_cycle,
        required=False,
    )

    pipeline.add_step(
        name="Write SQLite Refresh Marker",
        function=write_refresh_marker,
        required=True,
    )

    return pipeline


def run_daily_cycle():
    pipeline = build_daily_cycle_pipeline()
    return pipeline.run()


def main():
    return run_daily_cycle()


if __name__ == "__main__":
    main()
