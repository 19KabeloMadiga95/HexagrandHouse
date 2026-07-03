from __future__ import annotations

from src.services.results.lottery import (
    prepare_lottery_results,
    get_recent_lottery_results,
)
from src.services.results.football import (
    prepare_football_results,
    get_recent_football_results,
)
from src.services.results.backtesting import (
    prepare_backtest_results,
    get_result_accuracy,
)
from src.services.results.filtering import (
    get_lottery_game_options,
    get_football_league_options,
)
from src.services.results.formatting import format_short_date


def get_results_dashboard_data(days: int = 7) -> dict:
    lottery_df = prepare_lottery_results()
    football_df = prepare_football_results()
    backtest_df = prepare_backtest_results()

    recent_lottery_df = get_recent_lottery_results(lottery_df, days)
    recent_football_df = get_recent_football_results(football_df, days)

    latest_lottery_date = "-"
    latest_football_date = "-"

    if not recent_lottery_df.empty and "DrawDate" in recent_lottery_df.columns:
        latest_lottery_date = format_short_date(recent_lottery_df["DrawDate"].max())

    if not recent_football_df.empty and "MatchDate" in recent_football_df.columns:
        latest_football_date = format_short_date(recent_football_df["MatchDate"].max())

    return {
        "lottery_df": lottery_df,
        "football_df": football_df,
        "backtest_df": backtest_df,
        "recent_lottery_df": recent_lottery_df,
        "recent_football_df": recent_football_df,
        "lottery_game_options": get_lottery_game_options(recent_lottery_df),
        "football_league_options": get_football_league_options(recent_football_df),
        "kpis": {
            "lottery_results": len(recent_lottery_df),
            "football_results": len(recent_football_df),
            "latest_lottery_date": latest_lottery_date,
            "latest_football_date": latest_football_date,
            "scored_predictions": len(backtest_df),
            "result_accuracy": get_result_accuracy(backtest_df),
        },
    }