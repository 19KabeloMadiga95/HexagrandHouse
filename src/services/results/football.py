from __future__ import annotations

import pandas as pd

from src.data.database import read_football_history


def prepare_football_results() -> pd.DataFrame:
    df = read_football_history()

    if df.empty:
        return df

    df = df.copy()

    if "MatchDate" in df.columns:
        df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")

    for col in ["HomeGoals", "AwayGoals", "TotalGoals", "TotalCorners", "BTTS"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_recent_football_results(
    df: pd.DataFrame,
    days: int = 7,
) -> pd.DataFrame:
    if df.empty or "MatchDate" not in df.columns:
        return df

    today = pd.Timestamp.today().normalize()
    start_date = today - pd.Timedelta(days=days)

    df = df[df["MatchDate"] >= start_date].copy()

    if "HomeGoals" in df.columns and "AwayGoals" in df.columns:
        df = df[
            df["HomeGoals"].notna()
            & df["AwayGoals"].notna()
        ].copy()

    return df