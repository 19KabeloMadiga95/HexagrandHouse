from __future__ import annotations

from src.lottery.automation.run_daily_lottery_cycle import run_daily_lottery_cycle


# =========================================================
# FULL LOTTERY PIPELINE - SQLITE RUNTIME
# =========================================================


def run_full_lottery_pipeline() -> dict:
    """
    SQLite-first full lottery pipeline.

    The previous version orchestrated many Excel workbook generators.
    This runtime version keeps the production path clean:
    SQLite history -> SQLite features -> SQLite predictions -> SQLite ensemble.
    """

    return run_daily_lottery_cycle()


def main() -> dict:
    return run_full_lottery_pipeline()


if __name__ == "__main__":
    main()
