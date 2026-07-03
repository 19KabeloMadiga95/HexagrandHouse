from __future__ import annotations

import pandas as pd

from src.data.database import read_lottery_history
from src.services.lottery.display import add_game_display_column


def prepare_lottery_results() -> pd.DataFrame:
    df = read_lottery_history()

    if df.empty:
        return df

    df = add_game_display_column(df)

    if "DrawDate" in df.columns:
        df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")

    return df


def get_recent_lottery_results(
    df: pd.DataFrame,
    days: int = 7,
) -> pd.DataFrame:
    if df.empty or "DrawDate" not in df.columns:
        return df

    today = pd.Timestamp.today().normalize()
    start_date = today - pd.Timedelta(days=days)

    return df[df["DrawDate"] >= start_date].copy()