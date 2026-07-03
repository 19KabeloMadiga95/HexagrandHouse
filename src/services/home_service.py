from __future__ import annotations

import pandas as pd

from src.data.query_service import (
    get_platform_summary,
    get_recent_lottery_results,
    get_recent_football_results,
    get_latest_ensemble_predictions,
    health_check,
)


def get_total_platform_rows(db_summary_df: pd.DataFrame) -> int:
    if db_summary_df.empty:
        return 0

    return int(
        pd.to_numeric(
            db_summary_df["RowCount"],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )


def get_platform_status(platform_health: dict) -> str:
    if not platform_health.get("database_connected", False):
        return "Offline"

    if platform_health.get("tables", 0) < 5:
        return "Warning"

    return "Healthy"


def get_latest_lottery_result(lottery_df: pd.DataFrame) -> str:
    if lottery_df.empty:
        return "-"

    latest = lottery_df.iloc[0]

    game = latest.get(
        "GameName",
        latest.get("GameFamily", "Lottery"),
    )

    date_value = pd.to_datetime(
        latest.get("DrawDate"),
        errors="coerce",
    )

    if pd.isna(date_value):
        return str(game)

    return f"{game} — {date_value.strftime('%Y-%m-%d')}"


def get_top_football_play(predictions_df: pd.DataFrame) -> str:
    if predictions_df.empty:
        return "-"

    top = predictions_df.iloc[0]

    home = top.get("HomeTeam", "-")
    away = top.get("AwayTeam", "-")

    prediction = top.get(
        "PredictedResult",
        top.get(
            "ModelPick",
            top.get("BestResultPick", "Prediction"),
        ),
    )

    confidence = top.get(
        "EnsembleConfidenceScore",
        top.get("ConfidenceScore", "-"),
    )

    if confidence != "-":
        try:
            confidence = round(float(confidence), 2)
        except Exception:
            pass

    return f"{home} vs {away} — {prediction} ({confidence})"


def get_top_value_signal(predictions_df: pd.DataFrame) -> str:
    if predictions_df.empty:
        return "-"

    temp = predictions_df.copy()

    if "ValueScore" in temp.columns:
        temp["ValueScore"] = pd.to_numeric(
            temp["ValueScore"],
            errors="coerce",
        )

        temp = temp.sort_values(
            by="ValueScore",
            ascending=False,
        )

    top = temp.iloc[0]

    home = top.get("HomeTeam", "-")
    away = top.get("AwayTeam", "-")

    market = top.get(
        "Market",
        top.get(
            "PredictedResult",
            top.get("BestResultPick", "Top Signal"),
        ),
    )

    rating = top.get(
        "ValueRating",
        top.get("EnsembleConfidenceLabel", "Rated"),
    )

    return f"{home} vs {away} — {market} ({rating})"


def get_model_accuracy_value() -> str:
    return "-"


def get_home_dashboard_data() -> dict:
    lottery_df = get_recent_lottery_results(500)
    football_df = get_recent_football_results(500)
    predictions_df = get_latest_ensemble_predictions(100)
    db_summary_df = get_platform_summary()
    platform_health = health_check()

    total_rows = platform_health.get(
        "total_rows",
        get_total_platform_rows(db_summary_df),
    )

    return {
        "lottery_df": lottery_df,
        "football_df": football_df,
        "predictions_df": predictions_df,
        "db_summary_df": db_summary_df,
        "platform_health": platform_health,
        "platform_status": get_platform_status(platform_health),
        "total_rows": int(total_rows),
        "football_results_count": len(football_df),
        "model_accuracy": get_model_accuracy_value(),
        "top_play": get_top_football_play(predictions_df),
        "top_value_signal": get_top_value_signal(predictions_df),
        "latest_lottery_result": get_latest_lottery_result(lottery_df),
    }