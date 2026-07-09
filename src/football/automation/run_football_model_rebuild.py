from __future__ import annotations

from typing import Any

from src.football.automation.cycle_runner import CycleStep, run_logged_cycle
from src.football.features.export_football_features import export_football_features
from src.football.ingestion.sqlite_football_ingestion import update_football_fixtures_sqlite
from src.football.models.export_football_models import export_football_models
from src.football.predictions.sqlite_fixture_predictions import export_fixture_predictions
from src.football.reporting.football_model_performance_dashboard import (
    export_football_model_performance_dashboard,
)
from src.football.reporting.top_plays_report import export_top_plays_report
from src.football.value.value_bet_engine import export_value_bets


# =========================================================
# HEAVY FOOTBALL MODEL REBUILD CYCLE
# =========================================================
# This is the manual/weekly/monthly football rebuild.
# It is allowed to rebuild historical feature/model/backtest tables and can
# make the local development database large. Do not run this as the daily
# scheduled task unless you intentionally want a full model refresh.

PIPELINE_NAME = "SQLite Football Model Rebuild Cycle"


def build_cycle_steps() -> list[CycleStep]:
    return [
        CycleStep(
            name="Update Upcoming Football Fixtures",
            function=update_football_fixtures_sqlite,
            required=False,
        ),
        CycleStep(
            name="Build Historical Football Feature Tables",
            function=export_football_features,
            required=True,
        ),
        CycleStep(
            name="Generate Historical Football Model Tables",
            function=export_football_models,
            required=True,
        ),
        CycleStep(
            name="Refresh Football Model Performance Dashboard",
            function=export_football_model_performance_dashboard,
            required=True,
        ),
        CycleStep(
            name="Generate Current Fixture Predictions",
            function=export_fixture_predictions,
            required=False,
        ),
        CycleStep(
            name="Refresh Current Football Top Plays",
            function=export_top_plays_report,
            required=False,
        ),
        CycleStep(
            name="Refresh Current Football Value Bets",
            function=export_value_bets,
            required=False,
        ),
    ]


def run_football_model_rebuild() -> dict[str, Any]:
    return run_logged_cycle(
        pipeline_name=PIPELINE_NAME,
        title="HEXAGRANDHOUSE FOOTBALL MODEL REBUILD CYCLE",
        subtitle="Heavy feature/model/backtest rebuild mode",
        steps=build_cycle_steps(),
    )


def main() -> dict[str, Any]:
    return run_football_model_rebuild()


if __name__ == "__main__":
    main()
