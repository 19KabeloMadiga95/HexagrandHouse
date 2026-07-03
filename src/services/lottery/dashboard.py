from __future__ import annotations

from src.services.lottery.results import (
    prepare_lottery_results,
    get_latest_results,
    get_results_display_columns,
)
from src.services.lottery.predictions import (
    prepare_lottery_predictions,
    get_prediction_display_columns,
)
from src.services.lottery.filtering import get_game_options
from src.services.lottery.statistics import (
    get_lottery_kpis,
    get_result_coverage_summary,
)


def get_lottery_dashboard_data(limit: int = 300) -> dict:
    results_df = prepare_lottery_results(limit)
    predictions_df = prepare_lottery_predictions(limit)

    latest_results_df = get_latest_results(results_df, 12)

    coverage_df = get_result_coverage_summary(results_df)

    return {
        "results_df": results_df,
        "latest_results_df": latest_results_df,
        "predictions_df": predictions_df,
        "coverage_df": coverage_df,
        "game_options": get_game_options(results_df, predictions_df),
        "kpis": get_lottery_kpis(results_df, predictions_df),
        "display_columns": {
            "predictions": get_prediction_display_columns(predictions_df),
            "results": get_results_display_columns(latest_results_df),
        },
    }