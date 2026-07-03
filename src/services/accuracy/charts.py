from __future__ import annotations

import pandas as pd

from src.core.dataframe import first_existing_column


def build_accuracy_trend(history_df: pd.DataFrame) -> pd.DataFrame:
    if history_df.empty or "ResultHit" not in history_df.columns:
        return pd.DataFrame()

    date_col = first_existing_column(
        history_df,
        [
            "ResultDate",
            "FixtureDate",
            "MatchDate",
        ],
    )

    if date_col is None:
        return pd.DataFrame()

    trend_df = history_df.copy()

    trend_df[date_col] = pd.to_datetime(
        trend_df[date_col],
        errors="coerce",
    )

    trend_df = trend_df.dropna(subset=[date_col])

    trend_df = (
        trend_df
        .groupby(date_col)["ResultHit"]
        .mean()
        .reset_index()
    )

    trend_df["AccuracyPct"] = (
        pd.to_numeric(
            trend_df["ResultHit"],
            errors="coerce",
        ) * 100
    ).round(1)

    return trend_df.tail(20)


def get_sort_column(df: pd.DataFrame):
    return first_existing_column(
        df,
        [
            "ResultHitRate",
            "ResultAccuracy",
        ],
    )