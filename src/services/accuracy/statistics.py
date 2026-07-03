from __future__ import annotations

import pandas as pd

from src.core.dataframe import first_existing_column


def hit_rate(df: pd.DataFrame, column: str):
    if df.empty or column not in df.columns:
        return "-"

    value = pd.to_numeric(
        df[column],
        errors="coerce",
    ).mean()

    if pd.isna(value):
        return "-"

    return round(float(value) * 100, 1)


def build_kpis(history_df: pd.DataFrame) -> dict:
    return {
        "fixtures_scored": int(len(history_df)),
        "result_accuracy": hit_rate(history_df, "ResultHit"),
        "goals_accuracy": hit_rate(history_df, "GoalsHit"),
        "corners_accuracy": hit_rate(history_df, "CornersHit"),
    }