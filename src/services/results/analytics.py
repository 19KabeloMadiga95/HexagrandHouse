from __future__ import annotations

import pandas as pd


def get_lottery_volume(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    col = "GameDisplay" if "GameDisplay" in df.columns else "GameName"

    if col not in df.columns:
        return pd.DataFrame()

    result = (
        df.groupby(col)
        .size()
        .reset_index(name="Draws")
        .sort_values("Draws", ascending=False)
    )

    result = result.rename(columns={col: "Game"})

    return result


def get_football_result_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "ResultLabel" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("ResultLabel")
        .size()
        .reset_index(name="Matches")
        .sort_values("Matches", ascending=False)
    )