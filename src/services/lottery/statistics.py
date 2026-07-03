from __future__ import annotations

import pandas as pd


def get_lottery_kpis(
    results_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
) -> dict:
    latest_draw = "-"

    if not results_df.empty:
        latest = results_df.iloc[0]

        game = latest.get(
            "GameDisplay",
            latest.get("GameName", latest.get("GameFamily", "Lottery")),
        )

        draw_date = pd.to_datetime(
            latest.get("DrawDate"),
            errors="coerce",
        )

        if pd.notna(draw_date):
            latest_draw = f"{game} — {draw_date.strftime('%Y-%m-%d')}"
        else:
            latest_draw = str(game)

    game_count = 0

    if not results_df.empty and "GameDisplay" in results_df.columns:
        game_count = results_df["GameDisplay"].nunique()

    return {
        "latest_draw": latest_draw,
        "game_count": int(game_count),
        "result_count": int(len(results_df)),
        "prediction_count": int(len(predictions_df)),
    }


def get_result_coverage_summary(results_df: pd.DataFrame) -> pd.DataFrame:
    if results_df.empty:
        return pd.DataFrame()

    group_col = None

    for col in ["GameDisplay", "GameName", "GameFamily"]:
        if col in results_df.columns:
            group_col = col
            break

    if group_col is None:
        return pd.DataFrame()

    chart_df = (
        results_df[group_col]
        .value_counts()
        .reset_index()
    )

    chart_df.columns = ["Game", "Count"]

    return chart_df