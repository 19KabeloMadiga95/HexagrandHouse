from __future__ import annotations

import pandas as pd

from src.data.database import read_football_backtest_history


def prepare_backtest_results() -> pd.DataFrame:
    df = read_football_backtest_history()

    if df.empty:
        return df

    df = df.copy()

    if "FixtureDate" in df.columns:
        df["FixtureDate"] = pd.to_datetime(df["FixtureDate"], errors="coerce")

    for col in ["ResultHit", "GoalsHit", "CornersHit"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_result_accuracy(backtest_df: pd.DataFrame) -> str:
    if backtest_df.empty or "ResultHit" not in backtest_df.columns:
        return "-"

    value = pd.to_numeric(
        backtest_df["ResultHit"],
        errors="coerce",
    ).mean()

    if pd.isna(value):
        return "-"

    return f"{round(float(value) * 100, 1)}%"