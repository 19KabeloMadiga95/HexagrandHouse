from __future__ import annotations

from src.services.football.fixtures import (
    prepare_fixtures,
    get_fixture_display_columns,
)
from src.services.football.predictions import (
    prepare_football_predictions,
    get_top_predictions,
)
from src.services.football.value import (
    prepare_value_bets,
    get_value_display_columns,
)
from src.services.football.statistics import (
    get_league_count,
    get_average_confidence,
    get_league_fixture_summary,
    get_elite_prediction_count,
)
from src.services.football.filtering import get_league_options


def get_football_dashboard_data(limit: int = 500) -> dict:
    fixtures_df = prepare_fixtures(limit)
    predictions_df = prepare_football_predictions(limit)
    top_predictions_df = get_top_predictions(predictions_df, 12)
    value_bets_df = prepare_value_bets(predictions_df)

    league_summary_df = get_league_fixture_summary(fixtures_df)

    return {
        "fixtures_df": fixtures_df,
        "predictions_df": predictions_df,
        "top_predictions_df": top_predictions_df,
        "value_bets_df": value_bets_df,
        "league_summary_df": league_summary_df,
        "league_options": get_league_options(
            fixtures_df,
            predictions_df,
        ),
        "kpis": {
            "fixtures": int(len(fixtures_df)),
            "predictions": int(len(predictions_df)),
            "elite_predictions": get_elite_prediction_count(predictions_df),
            "leagues": get_league_count(
                fixtures_df,
                predictions_df,
            ),
            "average_confidence": get_average_confidence(predictions_df),
        },
        "display_columns": {
            "fixtures": get_fixture_display_columns(fixtures_df),
            "value": get_value_display_columns(value_bets_df),
        },
    }