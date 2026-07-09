from __future__ import annotations

from src.core.pipeline import BasePipeline
from src.lottery.automation.run_daily_lottery_cycle import main as run_lottery_cycle
from src.football.automation.run_daily_football_cycle import main as run_football_cycle
from src.automation.refresh_marker import main as write_refresh_marker


# =========================================================
# HEXAGRANDHOUSE DAILY CYCLE - SQLITE RUNTIME
# =========================================================


def build_daily_cycle_pipeline() -> BasePipeline:
    pipeline = BasePipeline("HexagrandHouse Daily Cycle - SQLite Runtime")

    pipeline.add_step(
        name="Lottery SQLite Daily Cycle",
        function=run_lottery_cycle,
        required=True,
    )

    pipeline.add_step(
        name="Football SQLite Daily Cycle",
        function=run_football_cycle,
        required=True,
    )

    pipeline.add_step(
        name="Write SQLite Refresh Marker",
        function=write_refresh_marker,
        required=False,
    )

    return pipeline


def run_daily_cycle():
    pipeline = build_daily_cycle_pipeline()
    return pipeline.run()


def main():
    return run_daily_cycle()


if __name__ == "__main__":
    main()
