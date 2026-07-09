from __future__ import annotations

from typing import Any

from src.football.automation.cycle_runner import CycleStep, run_logged_cycle
from src.football.ingestion.sqlite_football_ingestion import update_football_fixtures_sqlite
from src.football.predictions.sqlite_fixture_predictions import export_fixture_predictions
from src.football.reporting.top_plays_report import export_top_plays_report
from src.football.value.value_bet_engine import export_value_bets


# =========================================================
# LIGHTWEIGHT DAILY FOOTBALL FIXTURE CYCLE
# =========================================================
# This is the production/daily football refresh.
# It must stay lightweight:
#   - update upcoming fixtures
#   - generate current fixture predictions
#   - refresh current top plays and value bets
#   - clear stale outputs when no current fixtures exist
# It deliberately does NOT rebuild historical feature/model/backtest tables.
# Use run_football_model_rebuild.py for the heavy once-in-a-while rebuild.

PIPELINE_NAME = "SQLite Football Daily Fixture Cycle"


def build_cycle_steps() -> list[CycleStep]:
    return [
        CycleStep(
            name="Update Upcoming Football Fixtures",
            function=update_football_fixtures_sqlite,
            required=False,
        ),
        CycleStep(
            name="Generate Current Fixture Predictions",
            function=export_fixture_predictions,
            required=True,
        ),
        CycleStep(
            name="Refresh Current Football Top Plays",
            function=export_top_plays_report,
            required=True,
        ),
        CycleStep(
            name="Refresh Current Football Value Bets",
            function=export_value_bets,
            required=True,
        ),
    ]


def run_daily_football_cycle() -> dict[str, Any]:
    return run_logged_cycle(
        pipeline_name=PIPELINE_NAME,
        title="HEXAGRANDHOUSE FOOTBALL DAILY FIXTURE CYCLE",
        subtitle="Lightweight current-fixtures mode",
        steps=build_cycle_steps(),
    )


def main() -> dict[str, Any]:
    return run_daily_football_cycle()


if __name__ == "__main__":
    main()
