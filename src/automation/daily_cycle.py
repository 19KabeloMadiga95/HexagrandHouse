from __future__ import annotations

import importlib
from typing import Callable

from src.core.pipeline import BasePipeline


def load_callable(module_path: str, function_name: str = "main") -> Callable:
    module = importlib.import_module(module_path)

    if not hasattr(module, function_name):
        raise AttributeError(
            f"Module '{module_path}' does not have function '{function_name}'"
        )

    return getattr(module, function_name)


def build_daily_cycle_pipeline() -> BasePipeline:
    pipeline = BasePipeline("HexagrandHouse Daily Cycle")

    pipeline.add_step(
        name="Lottery Daily Cycle",
        function=load_callable(
            "src.lottery.automation.run_daily_lottery_cycle",
            "main",
        ),
        required=True,
    )

    pipeline.add_step(
        name="Football Daily Cycle",
        function=load_callable(
            "src.football.automation.run_daily_football_cycle",
            "main",
        ),
        required=True,
    )

    pipeline.add_step(
        name="Build HexagrandHouse Database",
        function=load_callable(
            "src.data.build_database",
            "main",
        ),
        required=True,
    )

    pipeline.add_step(
        name="Write Refresh Marker",
        function=load_callable(
            "src.automation.refresh_marker",
            "main",
        ),
        required=True,
    )

    return pipeline


def run_daily_cycle():
    pipeline = build_daily_cycle_pipeline()
    return pipeline.run()


def main():
    run_daily_cycle()


if __name__ == "__main__":
    main()